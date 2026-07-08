"""AI model configuration endpoints."""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_ai_model_config_service, get_llm_adapter
from scr.schemas.agent import AIModelConfigCreateDTO, AIModelConfigDTO
from scr.services.ai.llm_adapter import LLMAdapter
from scr.services.ai.model_config_service import AIModelConfigService


router = APIRouter(prefix="/ai/models", tags=["ai-models"])


@router.get("", response_model=list[AIModelConfigDTO], response_model_by_alias=True)
def list_ai_models(
    model_config_service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> list[AIModelConfigDTO]:
    """列出后端保存的 AI 模型配置，不返回 API Key。"""
    # API Key 只允许后端读取和调用模型，任何列表响应都必须走 public DTO。
    return model_config_service.list_public()


@router.put("/{model_id}", response_model=AIModelConfigDTO, response_model_by_alias=True)
def save_ai_model(
    model_id: str,
    payload: AIModelConfigCreateDTO,
    model_config_service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> AIModelConfigDTO:
    """保存 AI 模型配置。"""
    return model_config_service.save(model_id, payload)


@router.delete("/{model_id}", response_model=list[AIModelConfigDTO], response_model_by_alias=True)
def delete_ai_model(
    model_id: str,
    model_config_service: AIModelConfigService = Depends(get_ai_model_config_service),
) -> list[AIModelConfigDTO]:
    """删除 AI 模型配置。"""
    model_config_service.delete(model_id)
    return model_config_service.list_public()


@router.post("/{model_id}/test", response_model=dict, response_model_by_alias=True)
def test_ai_model(
    model_id: str,
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
) -> dict:
    """使用后端保存的密钥测试模型连接。"""
    return llm_adapter.test_connection(model_config_id=model_id)
