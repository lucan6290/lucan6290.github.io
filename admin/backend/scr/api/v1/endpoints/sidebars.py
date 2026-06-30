"""侧边栏端点。"""

from fastapi import APIRouter, Query

from scr.schemas.common import MutationPlanDTO
from scr.schemas.sidebar import SidebarStatusDTO, SidebarSyncDTO
from scr.services.content.sidebar_management_service import SidebarManagementService


router = APIRouter(prefix="/sidebars", tags=["sidebars"])
sidebar_management_service = SidebarManagementService()


@router.get("/status", response_model=SidebarStatusDTO)
def get_sidebar_status(include_details: bool = Query(default=True)) -> SidebarStatusDTO:
    """获取 docs 侧边栏对账状态。"""
    return sidebar_management_service.get_status(include_details=include_details)


@router.post("/sync", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_sidebars(payload: SidebarSyncDTO) -> MutationPlanDTO:
    """同步 docs 侧边栏；默认只返回计划。"""
    return sidebar_management_service.sync(payload)
