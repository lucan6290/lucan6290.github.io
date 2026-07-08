"""内容 Schema 端点。"""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_schema_service
from scr.infrastructure.registry.schema_service import SchemaService
from scr.schemas.common import MutationPlanDTO
from scr.schemas.schema import ContentSchemaDTO, SchemaInitDTO, SchemaInitResultDTO


router = APIRouter(prefix="/schema", tags=["schema"])


@router.get("", response_model=ContentSchemaDTO, response_model_exclude_none=True)
def get_schema(
    schema_service: SchemaService = Depends(get_schema_service),
) -> ContentSchemaDTO:
    """获取内容 Schema 汇总。"""
    return schema_service.get_schema()


@router.post(
    "/init",
    response_model=MutationPlanDTO | SchemaInitResultDTO,
    response_model_exclude_none=True,
)
def init_schema(
    payload: SchemaInitDTO,
    schema_service: SchemaService = Depends(get_schema_service),
) -> MutationPlanDTO | SchemaInitResultDTO:
    """初始化内容 Schema；默认只返回写入计划。"""
    return schema_service.init_schema(payload)
