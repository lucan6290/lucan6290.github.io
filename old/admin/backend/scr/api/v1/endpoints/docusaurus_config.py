"""Docusaurus 站点配置对账端点。"""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_docusaurus_config_management_service
from scr.schemas.common import MutationPlanDTO
from scr.schemas.docusaurus_config import DocusaurusConfigStatusDTO, DocusaurusConfigSyncDTO
from scr.services.content.docusaurus.docusaurus_config_management_service import DocusaurusConfigManagementService


router = APIRouter(prefix="/docusaurus-config", tags=["docusaurus-config"])


@router.get("/status", response_model=DocusaurusConfigStatusDTO, response_model_exclude_none=True)
def get_docusaurus_config_status(
    docusaurus_config_management_service: DocusaurusConfigManagementService = Depends(
        get_docusaurus_config_management_service
    ),
) -> DocusaurusConfigStatusDTO:
    """获取 docusaurus.config.ts navbar 与 docs/blog 内容的对账状态。"""
    return docusaurus_config_management_service.get_status()


@router.post("/sync", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_docusaurus_config(
    payload: DocusaurusConfigSyncDTO,
    docusaurus_config_management_service: DocusaurusConfigManagementService = Depends(
        get_docusaurus_config_management_service
    ),
) -> MutationPlanDTO:
    """同步 navbar：追加缺失的 docs 一级分类入口、清理断链；默认只返回计划。"""
    return docusaurus_config_management_service.sync(payload)
