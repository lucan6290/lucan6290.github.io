"""Backend-owned LLM adapter."""

from __future__ import annotations

import json
import re
from typing import Any

from scr.core.exceptions import AppError, BadRequestError
from scr.services.ai.model_config_service import AIModelConfigService


class LLMAdapter:
    """Call configured LLM providers through LangChain and normalize JSON responses."""

    def __init__(self, model_config_service: AIModelConfigService) -> None:
        self.model_config_service = model_config_service

    def generate_json(self, *, model_config_id: str | None, messages: list[dict[str, str]]) -> dict[str, Any]:
        llm, _ = self._chat_model(model_config_id=model_config_id, timeout=60)
        try:
            # 优先使用 JSON object 响应格式，降低模型返回 Markdown 包裹文本的概率。
            message = llm.invoke(messages, response_format={"type": "json_object"})
        except Exception as exc:
            raise AppError("AI 模型调用失败。", code="ai_model_call_failed") from exc

        content = self._content_to_text(getattr(message, "content", None))
        if not isinstance(content, str) or not content.strip():
            raise AppError("AI 模型响应为空。", code="ai_model_empty_response")
        return self._parse_json_content(content)

    def generate_tool_call(
        self,
        *,
        model_config_id: str | None,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        tool_name: str,
    ) -> dict[str, Any]:
        llm, _ = self._chat_model(model_config_id=model_config_id, timeout=60)
        try:
            message = llm.invoke(
                messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": tool_name}},
            )
        except Exception as exc:
            raise AppError("AI 模型调用失败。", code="ai_model_call_failed") from exc

        tool_calls = getattr(message, "tool_calls", None) or []
        for tool_call in tool_calls:
            if tool_call.get("name") != tool_name:
                continue
            arguments = tool_call.get("args")
            if isinstance(arguments, dict):
                parsed = arguments
            elif isinstance(arguments, str):
                parsed = self._parse_json_content(arguments)
            else:
                raise AppError("AI 模型工具调用参数为空。", code="ai_model_tool_arguments_invalid")
            return {"name": tool_name, "arguments": parsed, "raw": tool_call}

        content = self._content_to_text(getattr(message, "content", None))
        if isinstance(content, str) and content.strip():
            # 某些兼容服务会忽略 tool_choice，把工具参数直接放在 content 中。
            parsed = self._parse_json_content(content)
            return {"name": tool_name, "arguments": parsed, "raw": {"content": content}}
        raise AppError("AI 模型没有返回工具调用。", code="ai_model_tool_call_missing")

    def _chat_model(
        self,
        *,
        model_config_id: str | None,
        timeout: float,
    ) -> tuple[Any, Any]:
        try:
            from langchain_openai import ChatOpenAI
        except Exception as exc:
            raise AppError(
                "LangChain 依赖尚未安装，请先更新后端依赖。",
                code="langchain_not_installed",
            ) from exc

        model = self.model_config_service.get(model_config_id)
        if model.api_format != "openai":
            raise BadRequestError("暂只支持 OpenAI-compatible 模型配置。", code="ai_model_format_unsupported")
        if not model.api_key:
            raise BadRequestError("AI 模型配置缺少 API Key。", code="ai_model_api_key_missing")

        kwargs: dict[str, Any] = {
            "model": model.model_id,
            "api_key": model.api_key,
            "base_url": model.base_url,
            "temperature": model.temperature,
            "max_completion_tokens": model.max_tokens,
            "timeout": timeout,
        }
        if model.provider == "deepseek" and model.thinking_mode == "enabled":
            # DeepSeek 的思考模式属于 provider 扩展字段，只在对应供应商配置中注入。
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            kwargs["reasoning_effort"] = model.reasoning_effort
        return ChatOpenAI(**kwargs), model

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        # 兼容模型把 JSON 包在 ```json 代码块里的情况。
        fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fence:
            cleaned = fence.group(1).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AppError("AI 模型没有返回合法 JSON。", code="ai_model_json_invalid") from exc
        if not isinstance(parsed, dict):
            raise AppError("AI 模型 JSON 响应必须是对象。", code="ai_model_json_invalid")
        return parsed

    def test_connection(self, *, model_config_id: str) -> dict[str, Any]:
        llm, model = self._chat_model(model_config_id=model_config_id, timeout=30)
        try:
            llm.invoke([{"role": "user", "content": "Hi"}], temperature=0, max_completion_tokens=5)
        except Exception as exc:
            raise AppError("AI 模型连接测试失败。", code="ai_model_test_failed") from exc

        return {"success": True, "modelId": model.id}

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts)
        return ""
