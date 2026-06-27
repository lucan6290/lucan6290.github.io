"""AI model construction helpers."""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from .schemas import AIModelConfig


def validate_model_config(config: AIModelConfig) -> str | None:
    if not config.baseUrl or not config.apiKey or not config.modelId:
        return "请提供完整的模型配置（baseUrl / apiKey / modelId）"
    return None


def build_chat_model(config: AIModelConfig, *, streaming: bool = False, json_mode: bool = False) -> ChatOpenAI:
    is_deepseek = config.provider == "deepseek" or config.modelId.startswith("deepseek")
    thinking_enabled = is_deepseek and config.thinkingMode == "enabled"
    extra_body = {"thinking": {"type": config.thinkingMode}} if is_deepseek else None
    kwargs = {
        "base_url": config.baseUrl,
        "api_key": config.apiKey,
        "model": config.modelId,
        "max_tokens": config.maxTokens,
        "streaming": streaming,
        "extra_body": extra_body,
    }
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    if thinking_enabled:
        kwargs["reasoning_effort"] = config.reasoningEffort
    else:
        kwargs["temperature"] = config.temperature

    return ChatOpenAI(
        **kwargs,
    )
