"""站点内容校验端点。"""

from fastapi import APIRouter

from scr.schemas.validation import SiteValidationRequestDTO, SiteValidationResultDTO
from scr.services.content.validation_service import ValidationService


router = APIRouter(prefix="/validation", tags=["validation"])
validation_service = ValidationService()


@router.post("/site", response_model=SiteValidationResultDTO)
def validate_site(payload: SiteValidationRequestDTO) -> SiteValidationResultDTO:
    """执行 docs/blog 全站内容校验。"""
    return validation_service.validate_site(payload)
