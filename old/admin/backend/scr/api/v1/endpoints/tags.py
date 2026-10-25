"""标签端点。"""

from fastapi import APIRouter, Depends, Query

from scr.api.v1.dependencies import get_tag_service
from scr.infrastructure.registry.tag_service import TagService
from scr.schemas.tag import TagCreateDTO, TagDTO, TagSyncResultDTO


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagDTO], response_model_exclude_none=True)
def list_tags(
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    sort: str = Query(default="label"),
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagDTO]:
    """获取标签列表。"""
    return tag_service.list_tags(keyword=keyword, page=page, page_size=page_size, sort=sort)


@router.post("", response_model=TagDTO, response_model_exclude_none=True, status_code=201)
def create_tag(
    payload: TagCreateDTO,
    tag_service: TagService = Depends(get_tag_service),
) -> TagDTO:
    """创建标签并写入注册表。"""
    return tag_service.create_tag(payload)


@router.post("/sync", response_model=TagSyncResultDTO, response_model_exclude_none=True)
def sync_tags(
    dry_run: bool = Query(default=True),
    confirm: bool = Query(default=False),
    tag_service: TagService = Depends(get_tag_service),
) -> TagSyncResultDTO:
    """从文章 Front Matter 同步未注册标签。"""
    return tag_service.sync_tags(dry_run=dry_run, confirm=confirm)
