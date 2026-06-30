"""SQLite 注册表索引相关 DTO。"""

from typing import Any

from pydantic import BaseModel, Field


class RegistryIndexItemDTO(BaseModel):
    """管理索引中的单个通用实体。"""

    id: int
    entity_type: str
    entity_key: str
    slug: str | None = None
    title: str | None = None
    display_name: str | None = None
    description: str | None = None
    summary: str | None = None
    status: str
    visibility: str
    sort_order: int
    priority: int
    source_kind: str
    source_path: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    synced_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegistryIndexListResponseDTO(BaseModel):
    """通用实体分页响应。"""

    items: list[RegistryIndexItemDTO]
    page: int
    page_size: int
    total: int
    has_next: bool


class RegistryIndexSyncResultDTO(BaseModel):
    """索引同步结果。"""

    sync_id: int
    sync_type: str
    status: str
    database_path: str
    scanned_files: int
    changed_files: int
    upserted_entities: int
    deleted_entities: int
    error_count: int
    message: str | None = None


class RegistryIndexStatsDTO(BaseModel):
    """索引统计信息。"""

    database_path: str
    entity_counts: dict[str, int] = Field(default_factory=dict)
    article_count: int = 0
    category_count: int = 0
    tag_count: int = 0
    last_sync: dict[str, Any] | None = None


class RegistryYamlFileDTO(BaseModel):
    """YAML 注册表原文。"""

    registry_type: str
    path: str
    exists: bool
    content: str


class RegistryYamlSaveDTO(BaseModel):
    """保存 YAML 注册表原文请求。"""

    content: str
    rebuild_index: bool = True


class RegistryYamlEntriesDTO(BaseModel):
    """YAML 注册表条目列表。"""

    registry_type: str
    path: str
    exists: bool
    items: list[dict[str, Any]] = Field(default_factory=list)


class RegistryYamlEntriesSaveDTO(BaseModel):
    """保存 YAML 注册表条目列表请求。"""

    items: list[dict[str, Any]] = Field(default_factory=list)
    rebuild_index: bool = True


class RegistryDiffDTO(BaseModel):
    """YAML 注册表与 SQLite 索引差异。"""

    registry_type: str
    sqlite_entity_type: str
    yaml_count: int
    sqlite_count: int
    missing_in_sqlite: list[str] = Field(default_factory=list)
    missing_in_yaml: list[str] = Field(default_factory=list)
    checked_at: str
