"""分类实体索引器。"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.registry.registry_sqlite_repository import RegistrySqliteRepository


class RegistryCategoryIndexer:
    """将分类注册表内容写入 registry SQLite 索引。"""

    def __init__(
        self,
        repository: RegistrySqliteRepository,
        category_service: CategoryService | None = None,
    ) -> None:
        self.repository = repository
        self.category_service = category_service or CategoryService()

    def sync(self, conn: sqlite3.Connection) -> int:
        count = 0
        for article_type in [ArticleType.docs, ArticleType.blog]:
            categories = self.category_service.list_categories(
                article_type=article_type,
                include_empty=True,
                include_counts=True,
            )
            for category in self._flatten_categories(categories):
                self._upsert_category(conn, article_type, category)
                count += 1
        return count

    def _upsert_category(
        self,
        conn: sqlite3.Connection,
        article_type: ArticleType,
        category: CategoryDTO,
    ) -> None:
        path_key = "/".join(category.path)
        entity_key = f"{article_type.value}:{path_key}"
        metadata = {
            "type": article_type.value,
            "path": category.path,
            "cover": category.cover,
            "enabled": category.enabled,
        }
        entity_id = self.repository.upsert_entity(
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
            source_path=self.repository.relative_path(settings.content_schema_dir / "categories.yml"),
            metadata=metadata,
        )
        child_count = len(category.children)
        self.repository.upsert_category_detail(
            conn,
            entity_id=entity_id,
            path=entity_key,
            parent_path=f"{article_type.value}:{'/'.join(category.path[:-1])}" if len(category.path) > 1 else None,
            depth=len(category.path),
            slug=category.slug,
            label=category.label,
            full_label=" / ".join(category.path),
            description=category.description,
            article_count=category.article_count or 0,
            published_article_count=category.article_count or 0,
            child_count=child_count,
            is_leaf=child_count == 0,
            is_hidden=not category.enabled,
            extra=metadata,
        )

    @staticmethod
    def _flatten_categories(categories: Iterable[CategoryDTO]) -> list[CategoryDTO]:
        result: list[CategoryDTO] = []
        for category in categories:
            result.append(category)
            result.extend(RegistryCategoryIndexer._flatten_categories(category.children))
        return result
