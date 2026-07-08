"""文章 Markdown 索引器。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scr.models.article import ArticleType
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.infrastructure.registry.registry_sqlite_repository import RegistrySqliteRepository
from scr.infrastructure.registry.tag_slug_service import TagSlugService


class RegistryArticleIndexer:
    """扫描 docs/blog Markdown，并写入文章、文章分类、文章标签索引。"""

    def __init__(
        self,
        repository: RegistrySqliteRepository,
        filesystem: FileSystemService | None = None,
        markdown: MarkdownService | None = None,
        tag_slug_service: TagSlugService | None = None,
    ) -> None:
        self.repository = repository
        self.filesystem = filesystem or FileSystemService()
        self.markdown = markdown or MarkdownService()
        self.tag_slug_service = tag_slug_service or TagSlugService()

    def sync(self, conn: sqlite3.Connection) -> tuple[int, list[Path]]:
        count = 0
        files: list[Path] = []
        for article_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(article_type):
                files.append(path)
                self._upsert_article(conn, article_type, path)
                count += 1
        return count, files

    def _upsert_article(
        self,
        conn: sqlite3.Connection,
        article_type: ArticleType,
        path: Path,
    ) -> None:
        parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
        frontmatter = parsed.frontmatter
        relative_path = self.filesystem.relative_posix_path(article_type, path)
        title = self._optional_string(frontmatter.get("title")) or Path(relative_path).stem
        slug = self._article_slug(article_type, relative_path, frontmatter)
        description = self._optional_string(frontmatter.get("description"))
        updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        publication_status = "draft" if bool(frontmatter.get("draft", False)) else "published"
        category_paths = self._article_categories(article_type, relative_path, frontmatter)
        tag_slugs = [self.tag_slug_service.slug_from_label(tag) for tag in self._list_value(frontmatter.get("tags"))]
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

        entity_id = self.repository.upsert_entity(
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
            source_path=self.repository.relative_path(path),
            source_hash=self.repository.file_hash(path),
            source_mtime=int(path.stat().st_mtime),
            metadata=metadata,
            updated_at=updated_at,
        )
        self.repository.upsert_article_detail(
            conn,
            entity_id=entity_id,
            slug=slug,
            title=title,
            content_type=article_type.value,
            file_path=self.repository.relative_path(path),
            url_path=f"/docs/{slug}" if article_type == ArticleType.docs else f"/blog/{slug}",
            status=publication_status,
            excerpt=description,
            cover_image=self._optional_string(frontmatter.get("image")),
            author_key=self._first_value(frontmatter.get("authors")),
            word_count=word_count,
            reading_minutes=reading_minutes,
            published_at=self._optional_string(frontmatter.get("date")),
            created_at=self._optional_string(frontmatter.get("date")),
            updated_at=updated_at,
            frontmatter=frontmatter,
            extra=metadata,
        )
        self.repository.replace_article_categories(conn, article_entity_id=entity_id, category_paths=category_paths)
        self.repository.replace_article_tags(conn, article_entity_id=entity_id, tag_slugs=tag_slugs)

    @staticmethod
    def _article_slug(article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> str:
        if article_type == ArticleType.blog:
            slug = RegistryArticleIndexer._optional_string(frontmatter.get("slug"))
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

        parent = Path(relative_path).parent.as_posix()
        if not parent or parent == ".":
            return []
        top_category = parent.split("/", 1)[0].strip()
        return [f"{article_type.value}:{top_category}"] if top_category else []

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _first_value(value: Any) -> str | None:
        values = RegistryArticleIndexer._list_value(value)
        return values[0] if values else None

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
