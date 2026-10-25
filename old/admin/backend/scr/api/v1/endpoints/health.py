"""健康检查端点。

提供 /health 接口，供部署探活与版本核对使用。
"""

from fastapi import APIRouter

from scr.core.config import settings
from scr.schemas.common import HealthResponseDTO


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponseDTO)
def health_check() -> HealthResponseDTO:
    """返回服务状态、版本与运行环境。"""
    return HealthResponseDTO(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )
