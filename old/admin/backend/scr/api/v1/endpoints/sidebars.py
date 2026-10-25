"""侧边栏端点。"""

from fastapi import APIRouter, Depends, Query

from scr.api.v1.dependencies import get_blog_index_service, get_category_index_service, get_sidebar_management_service
from scr.schemas.common import MutationPlanDTO
from scr.schemas.sidebar import BlogIndexSyncDTO, DocsIndexSyncDTO, SidebarStatusDTO, SidebarSyncDTO, SidebarTargetType
from scr.services.content.blog.blog_index_service import BlogIndexService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.sidebars.sidebar_management_service import SidebarManagementService


router = APIRouter(prefix="/sidebars", tags=["sidebars"])


@router.get("/status", response_model=SidebarStatusDTO)
def get_sidebar_status(
    include_details: bool = Query(default=True),
    type: SidebarTargetType = Query(default="docs"),
    sidebar_management_service: SidebarManagementService = Depends(get_sidebar_management_service),
) -> SidebarStatusDTO:
    """获取 docs 或 blog 侧边栏对账状态。"""
    return sidebar_management_service.get_status(include_details=include_details, type=type)


@router.post("/sync", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_sidebars(
    payload: SidebarSyncDTO,
    sidebar_management_service: SidebarManagementService = Depends(get_sidebar_management_service),
) -> MutationPlanDTO:
    """同步 docs 侧边栏；默认只返回计划。"""
    return sidebar_management_service.sync(payload)


@router.post("/docs-index/sync", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_docs_index(
    payload: DocsIndexSyncDTO,
    category_index_service: CategoryIndexService = Depends(get_category_index_service),
) -> MutationPlanDTO:
    """同步 docs 一级分类目录页；默认只返回计划。"""
    return category_index_service.sync_all(dry_run=payload.dry_run, confirm=payload.confirm)


@router.post("/blog-index/sync", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_blog_index(
    payload: BlogIndexSyncDTO,
    blog_index_service: BlogIndexService = Depends(get_blog_index_service),
) -> MutationPlanDTO:
    """同步 blog 首页文档；默认只返回计划。"""
    return blog_index_service.sync_all(dry_run=payload.dry_run, confirm=payload.confirm)
