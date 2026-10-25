"""File-backed AI model configuration service."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.schemas.agent import AIModelConfigCreateDTO, AIModelConfigDTO, AIModelConfigInternalDTO


class AIModelConfigService:
    """Manage local AI model configuration for backend-owned LLM calls."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or settings.ai_model_config_path

    def list_public(self) -> list[AIModelConfigDTO]:
        return [self._to_public(model) for model in self._load()]

    def get(self, model_id: str | None) -> AIModelConfigInternalDTO:
        models = self._load()
        if model_id:
            for model in models:
                if model.id == model_id:
                    return model
            raise NotFoundError("AI 模型配置不存在。", code="ai_model_not_found", details={"model_id": model_id})

        default = next((model for model in models if model.is_default), None) or (models[0] if models else None)
        if default is None:
            raise NotFoundError("尚未配置 AI 模型。", code="ai_model_not_configured")
        return default

    def save(self, model_id: str, payload: AIModelConfigCreateDTO) -> AIModelConfigDTO:
        if model_id != payload.id:
            raise BadRequestError("路径模型 ID 与请求体 ID 不一致。", code="ai_model_id_mismatch")

        existing_models = self._load()
        existing = next((model for model in existing_models if model.id == model_id), None)
        data = payload.model_dump()
        if existing and not data.get("api_key"):
            # 编辑模型配置时允许前端不回传密钥，避免把旧 API Key 暴露到浏览器表单。
            data["api_key"] = existing.api_key

        models = [model for model in existing_models if model.id != model_id]
        models.append(AIModelConfigInternalDTO(**data))
        self._save(models)
        return self._to_public(models[-1])

    def delete(self, model_id: str) -> None:
        models = self._load()
        next_models = [model for model in models if model.id != model_id]
        if len(next_models) == len(models):
            raise NotFoundError("AI 模型配置不存在。", code="ai_model_not_found", details={"model_id": model_id})
        self._save(next_models)

    def _load(self) -> list[AIModelConfigInternalDTO]:
        if not self.config_path.exists():
            return self._env_defaults()

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BadRequestError("AI 模型配置文件格式错误。", code="ai_model_config_invalid") from exc

        raw_items = data.get("models", data) if isinstance(data, dict) else data
        if not isinstance(raw_items, list):
            raise BadRequestError("AI 模型配置文件必须是列表或包含 models 列表。", code="ai_model_config_invalid")
        return [AIModelConfigInternalDTO.model_validate(item) for item in raw_items]

    def _save(self, models: list[AIModelConfigInternalDTO]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"models": [model.model_dump(by_alias=True) for model in models]}
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _env_defaults(self) -> list[AIModelConfigInternalDTO]:
        # 首次启动没有配置文件时，从环境变量生成临时默认模型，不主动落盘密钥。
        deepseek_key = os.getenv("LUCHUAN_DEEPSEEK_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if deepseek_key:
            return [
                AIModelConfigInternalDTO(
                    id="deepseek-v4-pro-default",
                    name="DeepSeek V4 Pro",
                    provider="deepseek",
                    base_url=os.getenv("LUCHUAN_DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                    api_key=deepseek_key,
                    model_id=os.getenv("LUCHUAN_DEEPSEEK_MODEL", "deepseek-v4-pro"),
                    api_format="openai",
                    temperature=0.3,
                    max_tokens=8192,
                    thinking_mode="enabled",
                    reasoning_effort="max",
                    is_default=True,
                )
            ]
        if openai_key:
            return [
                AIModelConfigInternalDTO(
                    id="openai-default",
                    name="OpenAI Default",
                    provider="openai",
                    base_url=os.getenv("LUCHUAN_OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    api_key=openai_key,
                    model_id=os.getenv("LUCHUAN_OPENAI_MODEL", "gpt-4.1-mini"),
                    api_format="openai",
                    temperature=0.3,
                    max_tokens=4096,
                    is_default=True,
                )
            ]
        return []

    @staticmethod
    def _to_public(model: AIModelConfigInternalDTO) -> AIModelConfigDTO:
        # 统一出口隐藏 api_key，防止新增接口时误把密钥带回前端。
        return AIModelConfigDTO(**model.model_dump(exclude={"api_key"}))
