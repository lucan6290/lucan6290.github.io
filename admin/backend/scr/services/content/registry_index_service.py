"""SQLite 注册表索引服务。

YAML 与 Markdown 仍是内容源文件；本服务只维护可删除、可重建的后台查询索引，
用于搜索、分页、排序和统计。
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO
from scr.schemas.registry_index import (
    RegistryDiffDTO,
    RegistryIndexItemDTO,
    RegistryIndexListResponseDTO,
    RegistryIndexStatsDTO,
    RegistryIndexSyncResultDTO,
    RegistryYamlEntriesDTO,
    RegistryYamlEntriesSaveDTO,
    RegistryYamlFileDTO,
    RegistryYamlSaveDTO,
)
from scr.services.content.category_service import CategoryService
from scr.services.content.filesystem_service import FileSystemService
from scr.services.content.markdown_service import MarkdownService
from scr.services.content.tag_service import TagService


class RegistryIndexService:
    """维护 admin 后端的 SQLite 查询索引。"""

    schema_version = 1
    sortable_fields = {
        "entity_key": "entity_key",
        "title": "title",
        "display_name": "display_name",
        "status": "status",
        "sort_order": "sort_order",
        "priority": "priority",
        "updated_at": "updated_at",
        "synced_at": "synced_at",
    }
    registry_file_names = {
        "categories": "categories.yml",
        "tags": "tags.yml",
    }
    registry_top_keys = {
        "categories": "categories",
        "tags": "tags",
    }
    registry_entity_types = {
        "categories": "category",
        "tags": "tag",
    }

    def __init__(self) -> None:
        self.database_path = settings.registry_index_path
        self.category_service = CategoryService()
        self.tag_service = TagService()
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()

    def rebuild(self, *, sync_type: str = "full") -> RegistryIndexSyncResultDTO:
        """全量重建 SQLite 索引。"""
        started_at = self._now()
        scanned_files = 0
        upserted_entities = 0
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            self._ensure_schema(conn)
            sync_id = self._create_sync_run(conn, sync_type, started_at)
            try:
                conn.execute("DELETE FROM article_tags")
                conn.execute("DELETE FROM article_categories")
                conn.execute("DELETE FROM articles")
                conn.execute("DELETE FROM tags")
                conn.execute("DELETE FROM categories")
                conn.execute("DELETE FROM registry_entities")
                conn.execute("DELETE FROM source_files")
                self._clear_search(conn)

                category_count = self._sync_categories(conn)
                tag_count = self._sync_tags(conn)
                article_count, article_files = self._sync_articles(conn)
                scanned_files = self._sync_source_files(conn, article_files)
                upserted_entities = category_count + tag_count + article_count

                self._finish_sync_run(
                    conn,
                    sync_id,
                    status="success",
                    scanned_files=scanned_files,
                    changed_files=scanned_files,
                    upserted_entities=upserted_entities,
                    deleted_entities=0,
                    error_count=0,
                    message="索引重建完成。",
                )
                return self._sync_result(
                    sync_id=sync_id,
                    sync_type=sync_type,
                    status="success",
                    scanned_files=scanned_files,
                    changed_files=scanned_files,
                    upserted_entities=upserted_entities,
                    deleted_entities=0,
                    error_count=0,
                    message="索引重建完成。",
                )
            except Exception as exc:
                self._finish_sync_run(
                    conn,
                    sync_id,
                    status="failed",
                    scanned_files=scanned_files,
                    changed_files=0,
                    upserted_entities=upserted_entities,
                    deleted_entities=0,
                    error_count=1,
                    message=str(exc),
                    error_json=json.dumps({"error": str(exc)}, ensure_ascii=False),
                )
                raise

    def list_entities(
        self,
        *,
        entity_type: str | None = None,
        q: str | None = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
        sort: str = "updated_at",
        order: str = "desc",
    ) -> RegistryIndexListResponseDTO:
        """分页查询索引实体。"""
        self._validate_sort(sort)
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        offset = (page - 1) * page_size

        with self._connect() as conn:
            self._ensure_schema(conn)
            where_sql, params = self._build_entity_filters(entity_type=entity_type, status=status, q=q)
            total = int(conn.execute(f"SELECT COUNT(*) FROM registry_entities {where_sql}", params).fetchone()[0])
            rows = conn.execute(
                f"""
                SELECT *
                FROM registry_entities
                {where_sql}
                ORDER BY {self.sortable_fields[sort]} {order_sql}, id ASC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()

        return RegistryIndexListResponseDTO(
            items=[self._item_from_row(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            has_next=offset + len(rows) < total,
        )

    def stats(self) -> RegistryIndexStatsDTO:
        """返回索引整体统计。"""
        with self._connect() as conn:
            self._ensure_schema(conn)
            counts = {
                str(row["entity_type"]): int(row["count"])
                for row in conn.execute(
                    "SELECT entity_type, COUNT(*) AS count FROM registry_entities GROUP BY entity_type"
                ).fetchall()
            }
            last_sync_row = conn.execute(
                """
                SELECT id, sync_type, status, started_at, finished_at, scanned_files,
                       changed_files, upserted_entities, deleted_entities, error_count, message
                FROM sync_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        return RegistryIndexStatsDTO(
            database_path=str(self.database_path),
            entity_counts=counts,
            article_count=counts.get("article", 0),
            category_count=counts.get("category", 0),
            tag_count=counts.get("tag", 0),
            last_sync=dict(last_sync_row) if last_sync_row else None,
        )

    def get_yaml_file(self, registry_type: str) -> RegistryYamlFileDTO:
        """读取 YAML 注册表原文。"""
        path = self._registry_path(registry_type)
        return RegistryYamlFileDTO(
            registry_type=registry_type,
            path=self._relative_path(path),
            exists=path.exists(),
            content=path.read_text(encoding="utf-8") if path.exists() else self._empty_registry_content(registry_type),
        )

    def save_yaml_file(
        self,
        registry_type: str,
        payload: RegistryYamlSaveDTO,
    ) -> RegistryIndexSyncResultDTO | RegistryYamlFileDTO:
        """保存 YAML 原文，保存前先解析校验。"""
        self._parse_registry_content(registry_type, payload.content)
        path = self._registry_path(registry_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.content, encoding="utf-8")
        if payload.rebuild_index:
            return self.rebuild()
        return self.get_yaml_file(registry_type)

    def get_yaml_entries(self, registry_type: str) -> RegistryYamlEntriesDTO:
        """读取 YAML 注册表条目列表。"""
        path = self._registry_path(registry_type)
        content = path.read_text(encoding="utf-8") if path.exists() else self._empty_registry_content(registry_type)
        return RegistryYamlEntriesDTO(
            registry_type=registry_type,
            path=self._relative_path(path),
            exists=path.exists(),
            items=self._parse_registry_content(registry_type, content),
        )

    def save_yaml_entries(
        self,
        registry_type: str,
        payload: RegistryYamlEntriesSaveDTO,
    ) -> RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO:
        """保存 YAML 注册表条目列表。"""
        normalized = self._normalize_registry_type(registry_type)
        self._validate_registry_entries(normalized, payload.items)
        path = self._registry_path(registry_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = yaml.safe_dump(
            {self.registry_top_keys[normalized]: payload.items},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        path.write_text(content, encoding="utf-8")
        if payload.rebuild_index:
            return self.rebuild()
        return self.get_yaml_entries(registry_type)

    def diff_yaml_and_sqlite(self, registry_type: str) -> RegistryDiffDTO:
        """检查 YAML 注册表与 SQLite 索引的键差异。"""
        entries = self.get_yaml_entries(registry_type).items
        yaml_keys = {key for key in (self._registry_entry_key(registry_type, entry) for entry in entries) if key}
        sqlite_entity_type = self.registry_entity_types[self._normalize_registry_type(registry_type)]
        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT entity_key FROM registry_entities WHERE entity_type = ?",
                (sqlite_entity_type,),
            ).fetchall()
        sqlite_keys = {str(row["entity_key"]) for row in rows}
        return RegistryDiffDTO(
            registry_type=registry_type,
            sqlite_entity_type=sqlite_entity_type,
            yaml_count=len(yaml_keys),
            sqlite_count=len(sqlite_keys),
            missing_in_sqlite=sorted(yaml_keys - sqlite_keys),
            missing_in_yaml=sorted(sqlite_keys - yaml_keys),
            checked_at=self._now(),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _registry_path(self, registry_type: str) -> Path:
        normalized = self._normalize_registry_type(registry_type)
        return settings.content_schema_dir / self.registry_file_names[normalized]

    def _normalize_registry_type(self, registry_type: str) -> str:
        aliases = {
            "category": "categories",
            "categories": "categories",
            "tag": "tags",
            "tags": "tags",
        }
        normalized = aliases.get(registry_type.strip().lower())
        if not normalized:
            raise BadRequestError("注册表类型不支持。", code="invalid_registry_type", details={"registry_type": registry_type})
        return normalized

    def _empty_registry_content(self, registry_type: str) -> str:
        normalized = self._normalize_registry_type(registry_type)
        return yaml.safe_dump(
            {self.registry_top_keys[normalized]: []},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    def _parse_registry_content(self, registry_type: str, content: str) -> list[dict[str, Any]]:
        normalized = self._normalize_registry_type(registry_type)
        try:
            loaded = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise BadRequestError("YAML 注册表格式错误。", code="registry_yaml_invalid") from exc

        if isinstance(loaded, list):
            raw_items = loaded
        elif isinstance(loaded, dict):
            raw_items = loaded.get(self.registry_top_keys[normalized], [])
        else:
            raise BadRequestError("YAML 注册表格式错误。", code="registry_yaml_invalid")

        if not isinstance(raw_items, list):
            raise BadRequestError("YAML 注册表条目必须是列表。", code="registry_yaml_invalid")

        items: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise BadRequestError("YAML 注册表条目必须是对象。", code="registry_yaml_invalid")
            items.append(dict(item))
        self._validate_registry_entries(normalized, items)
        return items

    def _validate_registry_entries(self, registry_type: str, items: list[dict[str, Any]]) -> None:
        normalized = self._normalize_registry_type(registry_type)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise BadRequestError("YAML 注册表条目必须是对象。", code="registry_yaml_invalid", details={"index": index})
            if normalized == "categories" and not self._registry_entry_key(normalized, item):
                raise BadRequestError("分类条目必须包含 type 与 path/slug。", code="registry_yaml_invalid", details={"index": index})
            if normalized == "tags" and not str(item.get("slug") or "").strip():
                raise BadRequestError("标签条目必须包含 slug。", code="registry_yaml_invalid", details={"index": index})

    def _registry_entry_key(self, registry_type: str, entry: dict[str, Any]) -> str | None:
        normalized = self._normalize_registry_type(registry_type)
        if normalized == "categories":
            article_type = str(entry.get("type") or ArticleType.docs.value).strip()
            path = CategoryService._entry_path(entry)
            return f"{article_type}:{'/'.join(path)}" if article_type and path else None
        if normalized == "tags":
            slug = str(entry.get("slug") or "").strip()
            return slug or None
        return None

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS registry_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                slug TEXT,
                title TEXT,
                display_name TEXT,
                description TEXT,
                summary TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                visibility TEXT NOT NULL DEFAULT 'public',
                sort_order INTEGER NOT NULL DEFAULT 0,
                priority INTEGER NOT NULL DEFAULT 0,
                source_kind TEXT NOT NULL DEFAULT 'yaml',
                source_path TEXT,
                source_hash TEXT,
                source_mtime INTEGER,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT,
                synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_key)
            );

            CREATE TABLE IF NOT EXISTS categories (
                entity_id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                parent_path TEXT,
                depth INTEGER NOT NULL DEFAULT 0,
                slug TEXT NOT NULL,
                label TEXT NOT NULL,
                full_label TEXT,
                icon TEXT,
                color TEXT,
                description TEXT,
                seo_title TEXT,
                seo_description TEXT,
                article_count INTEGER NOT NULL DEFAULT 0,
                published_article_count INTEGER NOT NULL DEFAULT 0,
                draft_article_count INTEGER NOT NULL DEFAULT 0,
                child_count INTEGER NOT NULL DEFAULT 0,
                first_article_at TEXT,
                last_article_at TEXT,
                is_leaf INTEGER NOT NULL DEFAULT 1,
                is_featured INTEGER NOT NULL DEFAULT 0,
                is_hidden INTEGER NOT NULL DEFAULT 0,
                extra_json TEXT,
                FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tags (
                entity_id INTEGER PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                description TEXT,
                color TEXT,
                icon TEXT,
                article_count INTEGER NOT NULL DEFAULT 0,
                published_article_count INTEGER NOT NULL DEFAULT 0,
                draft_article_count INTEGER NOT NULL DEFAULT 0,
                first_article_at TEXT,
                last_article_at TEXT,
                is_featured INTEGER NOT NULL DEFAULT 0,
                is_hidden INTEGER NOT NULL DEFAULT 0,
                aliases_json TEXT,
                extra_json TEXT,
                FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS articles (
                entity_id INTEGER PRIMARY KEY,
                slug TEXT NOT NULL,
                title TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'blog',
                file_path TEXT NOT NULL UNIQUE,
                url_path TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                excerpt TEXT,
                cover_image TEXT,
                author_key TEXT,
                word_count INTEGER NOT NULL DEFAULT 0,
                reading_minutes INTEGER NOT NULL DEFAULT 0,
                published_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                frontmatter_json TEXT,
                extra_json TEXT,
                FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS article_categories (
                article_entity_id INTEGER NOT NULL,
                category_path TEXT NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(article_entity_id, category_path),
                FOREIGN KEY(article_entity_id) REFERENCES articles(entity_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS article_tags (
                article_entity_id INTEGER NOT NULL,
                tag_slug TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(article_entity_id, tag_slug),
                FOREIGN KEY(article_entity_id) REFERENCES articles(entity_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS source_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_kind TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT,
                file_size INTEGER,
                file_mtime INTEGER,
                last_synced_at TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                scanned_files INTEGER NOT NULL DEFAULT 0,
                changed_files INTEGER NOT NULL DEFAULT 0,
                upserted_entities INTEGER NOT NULL DEFAULT 0,
                deleted_entities INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                error_json TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_entities_type_key
            ON registry_entities(entity_type, entity_key);
            CREATE INDEX IF NOT EXISTS idx_entities_type_status
            ON registry_entities(entity_type, status);
            CREATE INDEX IF NOT EXISTS idx_entities_title
            ON registry_entities(title);
            CREATE INDEX IF NOT EXISTS idx_entities_updated_at
            ON registry_entities(updated_at);
            CREATE INDEX IF NOT EXISTS idx_categories_parent
            ON categories(parent_path);
            CREATE INDEX IF NOT EXISTS idx_categories_label
            ON categories(label);
            CREATE INDEX IF NOT EXISTS idx_categories_article_count
            ON categories(article_count DESC);
            CREATE INDEX IF NOT EXISTS idx_tags_name
            ON tags(name);
            CREATE INDEX IF NOT EXISTS idx_tags_normalized_name
            ON tags(normalized_name);
            CREATE INDEX IF NOT EXISTS idx_tags_article_count
            ON tags(article_count DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_status
            ON articles(status);
            CREATE INDEX IF NOT EXISTS idx_articles_published_at
            ON articles(published_at DESC);
            DROP INDEX IF EXISTS idx_templates_type;
            DROP INDEX IF EXISTS idx_templates_usage_count;
            DROP INDEX IF EXISTS idx_articles_template;
            DROP TABLE IF EXISTS templates;
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, description) VALUES (?, ?)",
            (self.schema_version, "registry index initial schema"),
        )
        self._ensure_search_table(conn)

    def _ensure_search_table(self, conn: sqlite3.Connection) -> None:
        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS registry_search USING fts5(
                    entity_type,
                    entity_key,
                    title,
                    display_name,
                    description,
                    summary,
                    tokenize='unicode61'
                )
                """
            )
        except sqlite3.OperationalError:
            # 某些 Python SQLite 构建未启用 FTS5；普通 LIKE 查询仍可工作。
            pass

    def _clear_search(self, conn: sqlite3.Connection) -> None:
        if self._table_exists(conn, "registry_search"):
            conn.execute("DELETE FROM registry_search")

    def _sync_categories(self, conn: sqlite3.Connection) -> int:
        count = 0
        for article_type in [ArticleType.docs, ArticleType.blog]:
            categories = self.category_service.list_categories(
                article_type=article_type,
                include_empty=True,
                include_counts=True,
            )
            for category in self._flatten_categories(categories):
                path_key = "/".join(category.path)
                entity_key = f"{article_type.value}:{path_key}"
                metadata = {
                    "type": article_type.value,
                    "path": category.path,
                    "cover": category.cover,
                    "enabled": category.enabled,
                }
                entity_id = self._upsert_entity(
                    conn,
                    entity_type="category",
                    entity_key=entity_key,
                    slug=category.slug,
                    title=category.label,
                    display_name=category.label,
                    description=category.description,
                    status="active" if category.enabled else "hidden",
                    sort_order=category.sort_order or 0,
                    source_kind="yaml",
                    source_path=self._relative_path(settings.content_schema_dir / "categories.yml"),
                    metadata=metadata,
                )
                child_count = len(category.children)
                conn.execute(
                    """
                    INSERT INTO categories(
                        entity_id, path, parent_path, depth, slug, label, full_label,
                        description, article_count, published_article_count, child_count,
                        is_leaf, is_hidden, extra_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity_id) DO UPDATE SET
                        path=excluded.path,
                        parent_path=excluded.parent_path,
                        depth=excluded.depth,
                        slug=excluded.slug,
                        label=excluded.label,
                        full_label=excluded.full_label,
                        description=excluded.description,
                        article_count=excluded.article_count,
                        published_article_count=excluded.published_article_count,
                        child_count=excluded.child_count,
                        is_leaf=excluded.is_leaf,
                        is_hidden=excluded.is_hidden,
                        extra_json=excluded.extra_json
                    """,
                    (
                        entity_id,
                        entity_key,
                        f"{article_type.value}:{'/'.join(category.path[:-1])}" if len(category.path) > 1 else None,
                        len(category.path),
                        category.slug,
                        category.label,
                        " / ".join(category.path),
                        category.description,
                        category.article_count or 0,
                        category.article_count or 0,
                        child_count,
                        0 if child_count else 1,
                        0 if category.enabled else 1,
                        self._json(metadata),
                    ),
                )
                count += 1
        return count

    def _sync_tags(self, conn: sqlite3.Connection) -> int:
        tags = self.tag_service.list_tags(page=1, page_size=10000, sort="label")
        for tag in tags:
            entity_id = self._upsert_entity(
                conn,
                entity_type="tag",
                entity_key=tag.slug,
                slug=tag.slug,
                title=tag.label,
                display_name=tag.label,
                description=tag.description,
                source_kind="yaml",
                source_path=self._relative_path(settings.content_schema_dir / "tags.yml"),
                metadata={"usage_count": tag.usage_count},
            )
            conn.execute(
                """
                INSERT INTO tags(
                    entity_id, slug, name, normalized_name, description,
                    article_count, published_article_count, extra_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET
                    slug=excluded.slug,
                    name=excluded.name,
                    normalized_name=excluded.normalized_name,
                    description=excluded.description,
                    article_count=excluded.article_count,
                    published_article_count=excluded.published_article_count,
                    extra_json=excluded.extra_json
                """,
                (
                    entity_id,
                    tag.slug,
                    tag.label,
                    tag.label.casefold(),
                    tag.description,
                    tag.usage_count,
                    tag.usage_count,
                    self._json({"usage_count": tag.usage_count}),
                ),
            )
        return len(tags)

    def _sync_articles(self, conn: sqlite3.Connection) -> tuple[int, list[Path]]:
        count = 0
        files: list[Path] = []
        for article_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(article_type):
                files.append(path)
                parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
                frontmatter = parsed.frontmatter
                relative_path = self.filesystem.relative_posix_path(article_type, path)
                title = self._optional_string(frontmatter.get("title")) or Path(relative_path).stem
                slug = self._article_slug(article_type, relative_path, frontmatter)
                description = self._optional_string(frontmatter.get("description"))
                updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
                publication_status = "draft" if bool(frontmatter.get("draft", False)) else "published"
                category_paths = self._article_categories(article_type, relative_path, frontmatter)
                tag_slugs = [self.tag_service._slug_from_label(tag) for tag in self._list_value(frontmatter.get("tags"))]
                body = parsed.body.strip()
                word_count = len(body.split())
                reading_minutes = max(1, round(word_count / 240)) if word_count else 0
                metadata = {
                    "type": article_type.value,
                    "publication_status": publication_status,
                    "relative_path": relative_path,
                    "tags": self._list_value(frontmatter.get("tags")),
                    "category_paths": category_paths,
                    "authors": self._list_value(frontmatter.get("authors")),
                }

                entity_id = self._upsert_entity(
                    conn,
                    entity_type="article",
                    entity_key=f"{article_type.value}:{relative_path}",
                    slug=slug,
                    title=title,
                    display_name=title,
                    description=description,
                    summary=body[:300] or None,
                    status="active",
                    source_kind="markdown",
                    source_path=self._relative_path(path),
                    source_hash=self._file_hash(path),
                    source_mtime=int(path.stat().st_mtime),
                    metadata=metadata,
                    updated_at=updated_at,
                )
                conn.execute(
                    """
                    INSERT INTO articles(
                        entity_id, slug, title, content_type, file_path, url_path, status,
                        excerpt, cover_image, author_key, word_count,
                        reading_minutes, published_at, created_at, updated_at,
                        frontmatter_json, extra_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity_id) DO UPDATE SET
                        slug=excluded.slug,
                        title=excluded.title,
                        content_type=excluded.content_type,
                        file_path=excluded.file_path,
                        url_path=excluded.url_path,
                        status=excluded.status,
                        excerpt=excluded.excerpt,
                        cover_image=excluded.cover_image,
                        author_key=excluded.author_key,
                        word_count=excluded.word_count,
                        reading_minutes=excluded.reading_minutes,
                        published_at=excluded.published_at,
                        created_at=excluded.created_at,
                        updated_at=excluded.updated_at,
                        frontmatter_json=excluded.frontmatter_json,
                        extra_json=excluded.extra_json
                    """,
                    (
                        entity_id,
                        slug,
                        title,
                        article_type.value,
                        self._relative_path(path),
                        f"/docs/{slug}" if article_type == ArticleType.docs else f"/blog/{slug}",
                        publication_status,
                        description,
                        self._optional_string(frontmatter.get("image")),
                        self._first_value(frontmatter.get("authors")),
                        word_count,
                        reading_minutes,
                        self._optional_string(frontmatter.get("date")),
                        self._optional_string(frontmatter.get("date")),
                        updated_at,
                        self._json(frontmatter),
                        self._json(metadata),
                    ),
                )
                for index, category_path in enumerate(category_paths):
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO article_categories(
                            article_entity_id, category_path, is_primary, sort_order
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (entity_id, category_path, 1 if index == 0 else 0, index),
                    )
                for index, tag_slug in enumerate(tag_slugs):
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO article_tags(article_entity_id, tag_slug, sort_order)
                        VALUES (?, ?, ?)
                        """,
                        (entity_id, tag_slug, index),
                    )
                count += 1
        return count, files

    def _sync_source_files(self, conn: sqlite3.Connection, article_files: list[Path]) -> int:
        files = [
            settings.content_schema_dir / "categories.yml",
            settings.content_schema_dir / "tags.yml",
            *article_files,
        ]
        synced_at = self._now()
        count = 0
        for path in files:
            if not path.exists():
                continue
            stat = path.stat()
            conn.execute(
                """
                INSERT INTO source_files(
                    source_kind, file_path, file_hash, file_size, file_mtime,
                    last_synced_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    source_kind=excluded.source_kind,
                    file_hash=excluded.file_hash,
                    file_size=excluded.file_size,
                    file_mtime=excluded.file_mtime,
                    last_synced_at=excluded.last_synced_at,
                    updated_at=excluded.updated_at,
                    last_error=NULL
                """,
                (
                    self._source_kind(path),
                    self._relative_path(path),
                    self._file_hash(path),
                    stat.st_size,
                    int(stat.st_mtime),
                    synced_at,
                    synced_at,
                ),
            )
            count += 1
        return count

    def _upsert_entity(
        self,
        conn: sqlite3.Connection,
        *,
        entity_type: str,
        entity_key: str,
        slug: str | None,
        title: str | None,
        display_name: str | None,
        description: str | None = None,
        summary: str | None = None,
        status: str = "active",
        visibility: str = "public",
        sort_order: int = 0,
        priority: int = 0,
        source_kind: str = "yaml",
        source_path: str | None = None,
        source_hash: str | None = None,
        source_mtime: int | None = None,
        metadata: dict[str, Any] | None = None,
        updated_at: str | None = None,
    ) -> int:
        now = self._now()
        conn.execute(
            """
            INSERT INTO registry_entities(
                entity_type, entity_key, slug, title, display_name, description, summary,
                status, visibility, sort_order, priority, source_kind, source_path,
                source_hash, source_mtime, metadata_json, created_at, updated_at, synced_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_type, entity_key) DO UPDATE SET
                slug=excluded.slug,
                title=excluded.title,
                display_name=excluded.display_name,
                description=excluded.description,
                summary=excluded.summary,
                status=excluded.status,
                visibility=excluded.visibility,
                sort_order=excluded.sort_order,
                priority=excluded.priority,
                source_kind=excluded.source_kind,
                source_path=excluded.source_path,
                source_hash=excluded.source_hash,
                source_mtime=excluded.source_mtime,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at,
                synced_at=excluded.synced_at
            """,
            (
                entity_type,
                entity_key,
                slug,
                title,
                display_name,
                description,
                summary,
                status,
                visibility,
                sort_order,
                priority,
                source_kind,
                source_path,
                source_hash,
                source_mtime,
                self._json(metadata or {}),
                now,
                updated_at or now,
                now,
            ),
        )
        row = conn.execute(
            "SELECT id FROM registry_entities WHERE entity_type = ? AND entity_key = ?",
            (entity_type, entity_key),
        ).fetchone()
        entity_id = int(row["id"])
        self._upsert_search(conn, entity_type, entity_key, title, display_name, description, summary)
        return entity_id

    def _upsert_search(
        self,
        conn: sqlite3.Connection,
        entity_type: str,
        entity_key: str,
        title: str | None,
        display_name: str | None,
        description: str | None,
        summary: str | None,
    ) -> None:
        if not self._table_exists(conn, "registry_search"):
            return
        conn.execute(
            """
            INSERT INTO registry_search(entity_type, entity_key, title, display_name, description, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entity_type, entity_key, title or "", display_name or "", description or "", summary or ""),
        )

    def _build_entity_filters(
        self,
        *,
        entity_type: str | None,
        status: str,
        q: str | None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if entity_type:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if status != "all":
            clauses.append("status = ?")
            params.append(status)
        if q:
            clauses.append(
                "(entity_key LIKE ? OR title LIKE ? OR display_name LIKE ? OR description LIKE ? OR summary LIKE ?)"
            )
            pattern = f"%{q}%"
            params.extend([pattern, pattern, pattern, pattern, pattern])
        return (f"WHERE {' AND '.join(clauses)}" if clauses else "", params)

    def _create_sync_run(self, conn: sqlite3.Connection, sync_type: str, started_at: str) -> int:
        cursor = conn.execute(
            "INSERT INTO sync_runs(sync_type, status, started_at) VALUES (?, ?, ?)",
            (sync_type, "running", started_at),
        )
        return int(cursor.lastrowid)

    def _finish_sync_run(
        self,
        conn: sqlite3.Connection,
        sync_id: int,
        *,
        status: str,
        scanned_files: int,
        changed_files: int,
        upserted_entities: int,
        deleted_entities: int,
        error_count: int,
        message: str | None,
        error_json: str | None = None,
    ) -> None:
        conn.execute(
            """
            UPDATE sync_runs
            SET status = ?, finished_at = ?, scanned_files = ?, changed_files = ?,
                upserted_entities = ?, deleted_entities = ?, error_count = ?,
                message = ?, error_json = ?
            WHERE id = ?
            """,
            (
                status,
                self._now(),
                scanned_files,
                changed_files,
                upserted_entities,
                deleted_entities,
                error_count,
                message,
                error_json,
                sync_id,
            ),
        )

    def _sync_result(
        self,
        *,
        sync_id: int,
        sync_type: str,
        status: str,
        scanned_files: int,
        changed_files: int,
        upserted_entities: int,
        deleted_entities: int,
        error_count: int,
        message: str | None,
    ) -> RegistryIndexSyncResultDTO:
        return RegistryIndexSyncResultDTO(
            sync_id=sync_id,
            sync_type=sync_type,
            status=status,
            database_path=str(self.database_path),
            scanned_files=scanned_files,
            changed_files=changed_files,
            upserted_entities=upserted_entities,
            deleted_entities=deleted_entities,
            error_count=error_count,
            message=message,
        )

    def _item_from_row(self, row: sqlite3.Row) -> RegistryIndexItemDTO:
        metadata = {}
        if row["metadata_json"]:
            try:
                metadata = json.loads(row["metadata_json"])
            except json.JSONDecodeError:
                metadata = {}
        return RegistryIndexItemDTO(
            id=int(row["id"]),
            entity_type=str(row["entity_type"]),
            entity_key=str(row["entity_key"]),
            slug=row["slug"],
            title=row["title"],
            display_name=row["display_name"],
            description=row["description"],
            summary=row["summary"],
            status=str(row["status"]),
            visibility=str(row["visibility"]),
            sort_order=int(row["sort_order"]),
            priority=int(row["priority"]),
            source_kind=str(row["source_kind"]),
            source_path=row["source_path"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            synced_at=str(row["synced_at"]),
            metadata=metadata,
        )

    def _validate_sort(self, sort: str) -> None:
        if sort not in self.sortable_fields:
            raise BadRequestError("sort 字段不支持。", code="invalid_sort_field", details={"sort": sort})

    @staticmethod
    def _flatten_categories(categories: Iterable[CategoryDTO]) -> list[CategoryDTO]:
        result: list[CategoryDTO] = []
        for category in categories:
            result.append(category)
            result.extend(RegistryIndexService._flatten_categories(category.children))
        return result

    @staticmethod
    def _article_slug(article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> str:
        if article_type == ArticleType.blog:
            slug = RegistryIndexService._optional_string(frontmatter.get("slug"))
            if slug:
                return slug
        return Path(relative_path).with_suffix("").as_posix()

    def _article_categories(
        self,
        article_type: ArticleType,
        relative_path: str,
        frontmatter: dict[str, Any],
    ) -> list[str]:
        if article_type == ArticleType.docs:
            parent = Path(relative_path).parent.as_posix()
            if parent and parent != ".":
                parts = parent.split("/")
                return [f"{article_type.value}:{'/'.join(parts[:index])}" for index in range(1, len(parts) + 1)]
            return []

        candidates = []
        candidates.extend(self._list_value(frontmatter.get("category")))
        candidates.extend(self._list_value(frontmatter.get("categories")))
        candidates.extend(self._list_value(frontmatter.get("tags")))
        path = self.category_service.resolve_article_category(article_type, [], candidates)[0]
        return [f"{article_type.value}:{'/'.join(path[:index])}" for index in range(1, len(path) + 1)]

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _first_value(value: Any) -> str | None:
        values = RegistryIndexService._list_value(value)
        return values[0] if values else None

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _source_kind(path: Path) -> str:
        if path.suffix.lower() in {".yml", ".yaml"}:
            return "yaml"
        if path.suffix.lower() in {".md", ".mdx"}:
            return "markdown"
        return "file"

    @staticmethod
    def _relative_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE name = ? AND type IN ('table', 'virtual table')",
            (name,),
        ).fetchone()
        return row is not None
