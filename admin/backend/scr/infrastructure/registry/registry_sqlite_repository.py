"""SQLite 仓储能力。

本模块只处理 registry index 的 SQLite 连接、schema、通用查询与写入。
上层服务负责决定索引哪些内容。
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scr.core.config import settings
from scr.schemas.registry_index import (
    RegistryIndexItemDTO,
    RegistryIndexListResponseDTO,
    RegistryIndexStatsDTO,
    RegistryIndexSyncResultDTO,
)
from scr.infrastructure.registry.registry_sqlite_mappers import (
    item_from_row as map_item_from_row,
    sync_result as build_sync_result,
)
from scr.infrastructure.registry.registry_sqlite_queries import (
    build_entity_filters as build_registry_entity_filters,
    table_exists as registry_table_exists,
    validate_sort as validate_registry_sort,
)
from scr.infrastructure.registry.registry_sqlite_schema import (
    SCHEMA_VERSION,
    SORTABLE_FIELDS,
    ensure_registry_schema,
    ensure_search_table as ensure_registry_search_table,
)


class RegistrySqliteRepository:
    """封装 registry index 的 SQLite 基础读写。"""

    schema_version = SCHEMA_VERSION
    sortable_fields = SORTABLE_FIELDS

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or settings.registry_index_path

    def connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def ensure_schema(self, conn: sqlite3.Connection) -> None:
        ensure_registry_schema(conn)

    def ensure_search_table(self, conn: sqlite3.Connection) -> None:
        ensure_registry_search_table(conn)

    def clear_all(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM article_tags")
        conn.execute("DELETE FROM article_categories")
        conn.execute("DELETE FROM articles")
        conn.execute("DELETE FROM tags")
        conn.execute("DELETE FROM categories")
        conn.execute("DELETE FROM registry_entities")
        conn.execute("DELETE FROM source_files")
        self.clear_search(conn)

    def clear_search(self, conn: sqlite3.Connection) -> None:
        if self.table_exists(conn, "registry_search"):
            conn.execute("DELETE FROM registry_search")

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
        self.validate_sort(sort)
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        offset = (page - 1) * page_size

        with self.connect() as conn:
            self.ensure_schema(conn)
            where_sql, params = self.build_entity_filters(entity_type=entity_type, status=status, q=q)
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
            items=[self.item_from_row(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            has_next=offset + len(rows) < total,
        )

    def stats(self) -> RegistryIndexStatsDTO:
        with self.connect() as conn:
            self.ensure_schema(conn)
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

    def entity_keys(self, conn: sqlite3.Connection, entity_type: str) -> set[str]:
        rows = conn.execute(
            "SELECT entity_key FROM registry_entities WHERE entity_type = ?",
            (entity_type,),
        ).fetchall()
        return {str(row["entity_key"]) for row in rows}

    def sync_source_files(self, conn: sqlite3.Connection, files: list[Path]) -> int:
        synced_at = self.now()
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
                    self.source_kind(path),
                    self.relative_path(path),
                    self.file_hash(path),
                    stat.st_size,
                    int(stat.st_mtime),
                    synced_at,
                    synced_at,
                ),
            )
            count += 1
        return count

    def upsert_entity(
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
        now = self.now()
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
                self.json(metadata or {}),
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
        self.upsert_search(conn, entity_type, entity_key, title, display_name, description, summary)
        return entity_id

    def upsert_category_detail(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: int,
        path: str,
        parent_path: str | None,
        depth: int,
        slug: str,
        label: str,
        full_label: str,
        description: str | None,
        article_count: int,
        published_article_count: int,
        child_count: int,
        is_leaf: bool,
        is_hidden: bool,
        extra: dict[str, Any],
    ) -> None:
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
                path,
                parent_path,
                depth,
                slug,
                label,
                full_label,
                description,
                article_count,
                published_article_count,
                child_count,
                1 if is_leaf else 0,
                1 if is_hidden else 0,
                self.json(extra),
            ),
        )

    def upsert_tag_detail(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: int,
        slug: str,
        name: str,
        description: str | None,
        article_count: int,
        published_article_count: int,
        extra: dict[str, Any],
    ) -> None:
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
                slug,
                name,
                name.casefold(),
                description,
                article_count,
                published_article_count,
                self.json(extra),
            ),
        )

    def upsert_article_detail(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: int,
        slug: str,
        title: str,
        content_type: str,
        file_path: str,
        url_path: str,
        status: str,
        excerpt: str | None,
        cover_image: str | None,
        author_key: str | None,
        word_count: int,
        reading_minutes: int,
        published_at: str | None,
        created_at: str | None,
        updated_at: str,
        frontmatter: dict[str, Any],
        extra: dict[str, Any],
    ) -> None:
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
                content_type,
                file_path,
                url_path,
                status,
                excerpt,
                cover_image,
                author_key,
                word_count,
                reading_minutes,
                published_at,
                created_at,
                updated_at,
                self.json(frontmatter),
                self.json(extra),
            ),
        )

    def replace_article_categories(
        self,
        conn: sqlite3.Connection,
        *,
        article_entity_id: int,
        category_paths: list[str],
    ) -> None:
        conn.execute("DELETE FROM article_categories WHERE article_entity_id = ?", (article_entity_id,))
        for index, category_path in enumerate(category_paths):
            conn.execute(
                """
                INSERT OR REPLACE INTO article_categories(
                    article_entity_id, category_path, is_primary, sort_order
                )
                VALUES (?, ?, ?, ?)
                """,
                (article_entity_id, category_path, 1 if index == 0 else 0, index),
            )

    def replace_article_tags(
        self,
        conn: sqlite3.Connection,
        *,
        article_entity_id: int,
        tag_slugs: list[str],
    ) -> None:
        conn.execute("DELETE FROM article_tags WHERE article_entity_id = ?", (article_entity_id,))
        for index, tag_slug in enumerate(tag_slugs):
            conn.execute(
                """
                INSERT OR REPLACE INTO article_tags(article_entity_id, tag_slug, sort_order)
                VALUES (?, ?, ?)
                """,
                (article_entity_id, tag_slug, index),
            )

    def upsert_search(
        self,
        conn: sqlite3.Connection,
        entity_type: str,
        entity_key: str,
        title: str | None,
        display_name: str | None,
        description: str | None,
        summary: str | None,
    ) -> None:
        if not self.table_exists(conn, "registry_search"):
            return
        conn.execute(
            """
            INSERT INTO registry_search(entity_type, entity_key, title, display_name, description, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entity_type, entity_key, title or "", display_name or "", description or "", summary or ""),
        )

    def create_sync_run(self, conn: sqlite3.Connection, sync_type: str, started_at: str) -> int:
        cursor = conn.execute(
            "INSERT INTO sync_runs(sync_type, status, started_at) VALUES (?, ?, ?)",
            (sync_type, "running", started_at),
        )
        return int(cursor.lastrowid)

    def finish_sync_run(
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
                self.now(),
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

    def sync_result(
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
        return build_sync_result(
            database_path=str(self.database_path),
            sync_id=sync_id,
            sync_type=sync_type,
            status=status,
            scanned_files=scanned_files,
            changed_files=changed_files,
            upserted_entities=upserted_entities,
            deleted_entities=deleted_entities,
            error_count=error_count,
            message=message,
        )

    def item_from_row(self, row: sqlite3.Row) -> RegistryIndexItemDTO:
        return map_item_from_row(row)

    def validate_sort(self, sort: str) -> None:
        validate_registry_sort(sort)

    def build_entity_filters(
        self,
        *,
        entity_type: str | None,
        status: str,
        q: str | None,
    ) -> tuple[str, list[Any]]:
        return build_registry_entity_filters(entity_type=entity_type, status=status, q=q)

    @staticmethod
    def json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def source_kind(path: Path) -> str:
        if path.suffix.lower() in {".yml", ".yaml"}:
            return "yaml"
        if path.suffix.lower() in {".md", ".mdx"}:
            return "markdown"
        return "file"

    @staticmethod
    def relative_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return registry_table_exists(conn, name)
