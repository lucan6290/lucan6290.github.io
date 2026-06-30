"""SQLite 注册表索引端点。"""

from fastapi import APIRouter, Query

from scr.schemas.registry_index import (
    RegistryDiffDTO,
    RegistryIndexListResponseDTO,
    RegistryIndexStatsDTO,
    RegistryIndexSyncResultDTO,
    RegistryYamlEntriesDTO,
    RegistryYamlEntriesSaveDTO,
    RegistryYamlFileDTO,
    RegistryYamlSaveDTO,
)
from scr.services.content.registry_index_service import RegistryIndexService


router = APIRouter(prefix="/registry-index", tags=["registry-index"])
registry_index_service = RegistryIndexService()


@router.post("/sync", response_model=RegistryIndexSyncResultDTO)
def rebuild_registry_index() -> RegistryIndexSyncResultDTO:
    """从 YAML 与 Markdown 全量重建 SQLite 管理索引。"""
    return registry_index_service.rebuild()


@router.get("/entities", response_model=RegistryIndexListResponseDTO, response_model_exclude_none=True)
def list_registry_entities(
    entity_type: str | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
    status: str = Query(default="active"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
) -> RegistryIndexListResponseDTO:
    """分页查询分类、标签、文章等通用索引实体。"""
    return registry_index_service.list_entities(
        entity_type=entity_type,
        q=q,
        status=status,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@router.get("/stats", response_model=RegistryIndexStatsDTO)
def get_registry_index_stats() -> RegistryIndexStatsDTO:
    """获取 SQLite 管理索引统计信息。"""
    return registry_index_service.stats()


@router.get("/yaml/{registry_type}", response_model=RegistryYamlFileDTO)
def get_registry_yaml(registry_type: str) -> RegistryYamlFileDTO:
    """读取 categories/tags YAML 注册表原文。"""
    return registry_index_service.get_yaml_file(registry_type)


@router.put("/yaml/{registry_type}", response_model=RegistryIndexSyncResultDTO | RegistryYamlFileDTO)
def save_registry_yaml(registry_type: str, payload: RegistryYamlSaveDTO) -> RegistryIndexSyncResultDTO | RegistryYamlFileDTO:
    """保存 YAML 注册表原文；默认保存后重建 SQLite 索引。"""
    return registry_index_service.save_yaml_file(registry_type, payload)


@router.get("/yaml/{registry_type}/entries", response_model=RegistryYamlEntriesDTO)
def get_registry_yaml_entries(registry_type: str) -> RegistryYamlEntriesDTO:
    """读取 YAML 注册表条目列表，用于表单化维护。"""
    return registry_index_service.get_yaml_entries(registry_type)


@router.put("/yaml/{registry_type}/entries", response_model=RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO)
def save_registry_yaml_entries(
    registry_type: str,
    payload: RegistryYamlEntriesSaveDTO,
) -> RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO:
    """保存 YAML 注册表条目列表；默认保存后重建 SQLite 索引。"""
    return registry_index_service.save_yaml_entries(registry_type, payload)


@router.get("/diff/{registry_type}", response_model=RegistryDiffDTO)
def get_registry_diff(registry_type: str) -> RegistryDiffDTO:
    """检查 YAML 注册表与 SQLite 索引之间的键差异。"""
    return registry_index_service.diff_yaml_and_sqlite(registry_type)
