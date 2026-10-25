"""发布端点。"""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_deploy_service
from scr.schemas.deploy import DeployRequestDTO, DeployResultDTO
from scr.services.site.deploy_service import DeployService


router = APIRouter(prefix="/deploy", tags=["deploy"])


@router.post("", response_model=DeployResultDTO)
def run_deploy(
    payload: DeployRequestDTO,
    deploy_service: DeployService = Depends(get_deploy_service),
) -> DeployResultDTO:
    """执行站点发布：可选构建、提交并推送到目标分支。"""
    return deploy_service.run_deploy(payload)
