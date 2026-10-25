"""LangChain-based editor Agent runner."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from scr.core.exceptions import AppError, BadRequestError
from scr.schemas.agent import EditorAgentRunRequestDTO
from scr.services.ai.model_config_service import AIModelConfigService
from scr.services.ai.tools.editor_toolkit import create_editor_agent_plan_tools


class EditorToolRuntime(Protocol):
    """Runtime tools exposed to the editor Agent."""

    last_operation_data: dict[str, Any] | None
    last_preview: dict[str, Any] | None

    def read_current_article(self) -> dict[str, Any]:
        ...

    def preview_current_article_edit(self, operation: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass
class EditorAgentPlanResult:
    operation_data: dict[str, Any]
    preview: dict[str, Any] | None = None
    tool_events: list[dict[str, Any]] = field(default_factory=list)


class EditorLangChainAgentRunner:
    """Run the editor Agent with the LangChain v1 agent harness."""

    def __init__(self, model_config_service: AIModelConfigService) -> None:
        self.model_config_service = model_config_service

    @staticmethod
    def is_available() -> bool:
        # 运行时探测依赖，避免本地只安装基础后端依赖时整个 FastAPI 应用启动失败。
        try:
            import langchain.agents  # noqa: F401
            import langchain_openai  # noqa: F401
        except Exception:
            return False
        return True

    def plan_current_article_edit(
        self,
        *,
        payload: EditorAgentRunRequestDTO,
        runtime: EditorToolRuntime,
    ) -> EditorAgentPlanResult:
        try:
            from langchain.agents import create_agent
            from langchain_openai import ChatOpenAI
        except Exception as exc:
            raise AppError(
                "LangChain 依赖尚未安装，请先更新后端依赖。",
                code="langchain_not_installed",
            ) from exc

        model = self.model_config_service.get(payload.model_config_id)
        if model.api_format != "openai":
            raise BadRequestError("暂只支持 OpenAI-compatible 模型配置。", code="ai_model_format_unsupported")
        if not model.api_key:
            raise BadRequestError("AI 模型配置缺少 API Key。", code="ai_model_api_key_missing")

        llm = ChatOpenAI(
            model=model.model_id,
            api_key=model.api_key,
            base_url=model.base_url,
            temperature=model.temperature,
            max_completion_tokens=model.max_tokens,
        )
        agent = create_agent(
            model=llm,
            tools=create_editor_agent_plan_tools(runtime),
            system_prompt=self._system_prompt(),
        )
        result = agent.invoke(
            {"messages": [{"role": "user", "content": self._user_prompt(payload)}]},
            config={"recursion_limit": 12},
        )
        # LangChain 返回完整消息轨迹，这里提取工具调用给前端事件流使用，不影响最终写入逻辑。
        tool_events = self._collect_tool_events(result)

        if runtime.last_operation_data is None:
            # 预览工具是安全闸：没有经过预览的 operation 不能进入后续写入流程。
            raise AppError("Agent 没有调用编辑预览工具。", code="agent_tool_call_missing")
        return EditorAgentPlanResult(
            operation_data=runtime.last_operation_data,
            preview=runtime.last_preview,
            tool_events=tool_events,
        )

    @staticmethod
    def _collect_tool_events(agent_result: Any) -> list[dict[str, Any]]:
        messages = agent_result.get("messages", []) if isinstance(agent_result, dict) else []
        tool_calls_by_id: dict[str, dict[str, Any]] = {}
        events: list[dict[str, Any]] = []

        # 先记录 AI 发出的 tool_call，再把后续 tool message 按 id 合并成一条可展示事件。
        for message in messages:
            for tool_call in getattr(message, "tool_calls", None) or []:
                name = tool_call.get("name")
                if not name:
                    continue
                call_id = tool_call.get("id") or name
                tool_calls_by_id[call_id] = {"tool": name, "args": tool_call.get("args") or {}}

            if getattr(message, "type", None) != "tool":
                continue
            call_id = getattr(message, "tool_call_id", None) or getattr(message, "id", None)
            event = dict(tool_calls_by_id.get(call_id, {}))
            event.setdefault("tool", getattr(message, "name", None) or call_id or "tool")
            event.setdefault("args", {})
            event["result"] = EditorLangChainAgentRunner._parse_tool_message_content(getattr(message, "content", None))
            events.append(event)
        return events

    @staticmethod
    def _parse_tool_message_content(content: Any) -> Any:
        if not isinstance(content, str):
            return content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    @staticmethod
    def _system_prompt() -> str:
        return (
            "你是博客编辑器 Agent。你必须通过工具完成工作："
            "第一步调用 read_current_article 读取当前文章；"
            "第二步根据用户要求生成 operation，并调用 preview_current_article_edit 获取 diff。"
            "不要直接声称已写入文件。不要调用不存在的工具。"
            "operation.type 只能是 insert, replace, delete, rewrite, frontmatter；"
            "operation.scope 只能是 document, selection, frontmatter；"
            "insertPosition 只能是 append, prepend, before_old_text, after_old_text。"
        )

    @staticmethod
    def _user_prompt(payload: EditorAgentRunRequestDTO) -> str:
        return json.dumps(
            {
                "userInput": payload.user_input,
                "approvalMode": payload.approval_mode,
                "selection": payload.selection.model_dump(by_alias=True) if payload.selection else None,
                "command": payload.command,
            },
            ensure_ascii=False,
        )
