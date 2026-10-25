"""SQLite 注册表索引服务。

YAML 与 Markdown 仍是内容源文件；本服务只维护可删除、可重建的后台查询索引，
用于搜索、分页、排序和统计。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from scr.core.config import settings
from scr.schemas.registry_index import (
    RegistryDiffDTO,
    RegistryIndexListResponseDTO,
    RegistryIndexStatsDTO,
    RegistryIndexSyncResultDTO,
)
from scr.infrastructure.registry.registry_article_indexer import RegistryArticleIndexer
from scr.infrastructure.registry.registry_category_indexer import RegistryCategoryIndexer
from scr.infrastructure.registry.registry_sqlite_repository import RegistrySqliteRepository
from scr.infrastructure.registry.registry_tag_indexer import RegistryTagIndexer
from scr.infrastructure.registry.registry_yaml_service import RegistryYamlService


class RegistryIndexService:
    """维护 admin 后端的 SQLite 查询索引。"""

    registry_entity_types = {
        "categories": "category",
        "tags": "tag",
    }

    def __init__(self) -> None:
        self.repository = RegistrySqliteRepository()
        self.database_path = self.repository.database_path
        self.yaml = RegistryYamlService()
        self.category_indexer = RegistryCategoryIndexer(self.repository)
        self.tag_indexer = RegistryTagIndexer(self.repository)
        self.article_indexer = RegistryArticleIndexer(self.repository)

    def rebuild(self, *, sync_type: str = "full") -> RegistryIndexSyncResultDTO:
        """全量重建 SQLite 索引。"""
        started_at = self._now()
        scanned_files = 0
        upserted_entities = 0

        with self.repository.connect() as conn:
            self.repository.ensure_schema(conn)
            sync_id = self.repository.create_sync_run(conn, sync_type, started_at)
            try:
                self.repository.clear_all(conn)

                category_count = self.category_indexer.sync(conn)
                tag_count = self.tag_indexer.sync(conn)
                article_count, article_files = self.article_indexer.sync(conn)
                scanned_files = self.repository.sync_source_files(
                    conn,
                    [
                        settings.content_schema_dir / "categories.yml",
                        settings.content_schema_dir / "tags.yml",
                        *article_files,
                    ],
                )
                upserted_entities = category_count + tag_count + article_count

                self.repository.finish_sync_run(
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
                return self.repository.sync_result(
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
                self.repository.finish_sync_run(
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
        return self.repository.list_entities(
            entity_type=entity_type,
            q=q,
            status=status,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )

    def stats(self) -> RegistryIndexStatsDTO:
        """返回索引整体统计。"""
        return self.repository.stats()

    def diff_yaml_and_sqlite(self, registry_type: str) -> RegistryDiffDTO:
        """检查 YAML 注册表与 SQLite 索引的键差异。"""
        entries = self.yaml.get_yaml_entries(registry_type).items
        yaml_keys = {key for key in (self.yaml.registry_entry_key(registry_type, entry) for entry in entries) if key}
        sqlite_entity_type = self.registry_entity_types[self.yaml.normalize_registry_type(registry_type)]
        with self.repository.connect() as conn:
            self.repository.ensure_schema(conn)
            sqlite_keys = self.repository.entity_keys(conn, sqlite_entity_type)
        return RegistryDiffDTO(
            registry_type=registry_type,
            sqlite_entity_type=sqlite_entity_type,
            yaml_count=len(yaml_keys),
            sqlite_count=len(sqlite_keys),
            missing_in_sqlite=sorted(yaml_keys - sqlite_keys),
            missing_in_yaml=sorted(sqlite_keys - yaml_keys),
            checked_at=self._now(),
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
