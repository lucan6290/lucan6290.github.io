"""站点内容校验端点。"""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_validation_service
from scr.schemas.validation import SiteValidationRequestDTO, SiteValidationResultDTO
from scr.services.content.validation.validation_service import ValidationService


router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/site", response_model=SiteValidationResultDTO)
def validate_site(
    payload: SiteValidationRequestDTO,
    validation_service: ValidationService = Depends(get_validation_service),
) -> SiteValidationResultDTO:
    """执行 docs/blog 全站内容校验。"""
    return validation_service.validate_site(payload)
