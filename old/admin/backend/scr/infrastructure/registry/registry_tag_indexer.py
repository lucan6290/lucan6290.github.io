"""标签实体索引器。"""

from __future__ import annotations

import sqlite3

from scr.core.config import settings
from scr.infrastructure.registry.registry_sqlite_repository import RegistrySqliteRepository
from scr.infrastructure.registry.tag_service import TagService


class RegistryTagIndexer:
    """将标签注册表与使用量写入 registry SQLite 索引。"""

    def __init__(
        self,
        repository: RegistrySqliteRepository,
        tag_service: TagService | None = None,
    ) -> None:
        self.repository = repository
        self.tag_service = tag_service or TagService()

    def sync(self, conn: sqlite3.Connection) -> int:
        tags = self.tag_service.list_tags(page=1, page_size=10000, sort="label")
        for tag in tags:
            entity_id = self.repository.upsert_entity(
                conn,
                entity_type="tag",
                entity_key=tag.slug,
                slug=tag.slug,
                title=tag.label,
                display_name=tag.label,
                description=tag.description,
                source_kind="yaml",
                source_path=self.repository.relative_path(settings.content_schema_dir / "tags.yml"),
                metadata={"usage_count": tag.usage_count},
            )
            self.repository.upsert_tag_detail(
                conn,
                entity_id=entity_id,
                slug=tag.slug,
                name=tag.label,
                description=tag.description,
                article_count=tag.usage_count,
                published_article_count=tag.usage_count,
                extra={"usage_count": tag.usage_count},
            )
        return len(tags)
