"""Editor article Agent orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.schemas.agent import (
    AgentEventDTO,
    AgentRunResponseDTO,
    ApprovalResumeRequestDTO,
    EditorAgentOperationDTO,
    EditorAgentRunRequestDTO,
)
from scr.services.ai.llm_adapter import LLMAdapter
from scr.services.ai.tools.editor_article_runtime import EditorArticleToolRuntime
from scr.services.ai.tools.editor_operation import (
    format_operation_validation_errors,
    normalize_operation,
    parse_operation_data,
    stable_hash,
)
from scr.services.ai.tools.get_current_selection import get_current_selection
from scr.services.ai.tools.preview_current_article_edit import preview_current_article_edit
from scr.services.ai.tools.propose_article_edit import editor_operation_tool_schema
from scr.services.ai.tools.read_current_article import read_current_article
from scr.services.ai.tools.write_current_article import write_current_article
from scr.services.content.articles.article_service import ArticleService


@dataclass
class PendingApproval:
    """一次待审批写入的最小恢复上下文。"""

    session_id: str
    approval_id: str
    payload_hash: str
    request: EditorAgentRunRequestDTO


class EditorAgentService:
    """Run the editor article Agent against the existing article workflow."""

    def __init__(self, *, article_service: ArticleService, llm_adapter: LLMAdapter, agent_runner: Any | None = None) -> None:
        self.article_service = article_service
        self.llm_adapter = llm_adapter
        self.agent_runner = agent_runner
        self._approvals: dict[str, PendingApproval] = {}

    def run(self, payload: EditorAgentRunRequestDTO) -> AgentRunResponseDTO:
        session_id = payload.session_id or self._new_session_id()
        events = [self._event("session", "编辑器 Agent 会话已开始。", {"sessionId": session_id})]

        if payload.command == "read_current_article":
            return self._read_current_article(session_id, payload, events)
        if payload.command == "get_current_selection":
            return self._get_current_selection(session_id, payload, events)
        if payload.command == "plan_current_article_edit":
            return self._plan_current_article_edit(session_id, payload, events)
        if payload.command == "preview_current_article_edit":
            return self._preview_current_article_edit(session_id, payload, events)
        if payload.command == "write_current_article":
            return self._write_current_article(session_id, payload, events)
        raise BadRequestError("不支持的编辑器 Agent 命令。", code="agent_command_unsupported")

    def resume_approval(self, approval_id: str, payload: ApprovalResumeRequestDTO) -> AgentRunResponseDTO:
        pending = self._approvals.get(approval_id)
        if pending is None:
            raise NotFoundError("审批记录不存在或已过期。", code="approval_not_found")
        # 同时校验 session 与 payload hash，避免用户确认的是旧文章版本或旧编辑方案。
        if pending.session_id != payload.session_id or pending.payload_hash != payload.payload_hash:
            raise ConflictError("审批上下文已变化，请重新生成方案。", code="approval_context_conflict")
        if not payload.approved:
            self._approvals.pop(approval_id, None)
            return AgentRunResponseDTO(
                session_id=payload.session_id,
                agent_type="editor",
                status="failed",
                events=[
                    self._event("approval_required", "用户拒绝了本次写入。"),
                    self._event("done", "编辑器 Agent 已停止。"),
                ],
                result={"message": "用户拒绝了本次写入。"},
            )

        next_request = pending.request.model_copy(update={"confirmed": True})
        self._approvals.pop(approval_id, None)
        return self._write_current_article(
            payload.session_id,
            next_request,
            [self._event("session", "审批已确认，继续执行写入。", {"approvalId": approval_id})],
        )

    def _read_current_article(
        self,
        session_id: str,
        payload: EditorAgentRunRequestDTO,
        events: list[AgentEventDTO],
    ) -> AgentRunResponseDTO:
        article = self._get_article(payload.article_path)
        events.append(self._event("tool_result", "已读取当前文章。", {"articleId": article.id, "version": article.version}))
        return self._completed(session_id, events, read_current_article(article))

    def _get_current_selection(
        self,
        session_id: str,
        payload: EditorAgentRunRequestDTO,
        events: list[AgentEventDTO],
    ) -> AgentRunResponseDTO:
        events.append(self._event("tool_result", "已读取当前选区。"))
        return self._completed(session_id, events, get_current_selection(payload))

    def _plan_current_article_edit(
        self,
        session_id: str,
        payload: EditorAgentRunRequestDTO,
        events: list[AgentEventDTO],
    ) -> AgentRunResponseDTO:
        if not payload.user_input or not payload.user_input.strip():
            raise BadRequestError("缺少编辑指令。", code="agent_user_input_required")
        article = self._get_article(payload.article_path)
        events.append(self._event("tool_result", "已读取当前文章。", {"articleId": article.id, "version": article.version}))
        events.append(self._event("tool_call", "正在请求模型生成结构化编辑方案。"))

        runtime = EditorArticleToolRuntime(payload=payload, article=article)
        agent_plan = self._run_langchain_agent_plan(payload, runtime)
        if agent_plan is not None:
            # LangChain 路径会真实调用工具，保留工具事件给前端展示 Agent 的执行轨迹。
            for tool_event in agent_plan.tool_events:
                events.append(self._event("tool_call", f"Agent 调用了工具：{tool_event['tool']}。", tool_event))
            operation_data = agent_plan.operation_data
            preview = agent_plan.preview
        else:
            # 依赖不可用时退回一次 LLM 调用，仍要求模型返回同一个结构化 operation。
            operation_data = self._generate_operation_with_tool_call(payload, article.frontmatter, article.body)
            preview = None

        try:
            operation = parse_operation_data(operation_data)
        except ValidationError as exc:
            validation_errors = format_operation_validation_errors(exc)
            events.append(self._event("error", "模型返回的编辑操作格式不合法。", {"validationErrors": validation_errors}))
            events.append(self._event("done", "编辑方案未生成。"))
            return AgentRunResponseDTO(
                session_id=session_id,
                agent_type="editor",
                status="failed",
                events=events,
                result={
                    "message": "模型返回的编辑操作格式不合法，请换一种说法重试。",
                    "operation": operation_data if isinstance(operation_data, dict) else None,
                    "validationErrors": validation_errors,
                    "warnings": [],
                },
            )
        operation = normalize_operation(payload, operation, article.body)
        # 无论 operation 来自 Agent 工具还是普通模型调用，写入前都先用同一套预览逻辑产出 diff 与风险标记。
        preview = preview or preview_current_article_edit(
            body=article.body,
            frontmatter=article.frontmatter,
            operation=operation,
            current_hash=article.version,
        )
        if preview["validationErrors"]:
            events.append(self._event("error", "编辑方案校验失败。", {"validationErrors": preview["validationErrors"]}))
            events.append(self._event("done", "编辑方案未生成。"))
            return AgentRunResponseDTO(
                session_id=session_id,
                agent_type="editor",
                status="failed",
                events=events,
                result={
                    "message": "编辑方案不合法，请调整指令后重试。",
                    "operation": operation.model_dump(by_alias=True),
                    "preview": preview,
                    "validationErrors": preview["validationErrors"],
                    "warnings": [],
                },
            )
        events.append(self._event("tool_result", "已生成编辑预览。", {"riskFlags": preview["riskFlags"]}))
        events.append(self._event("done", "编辑方案已生成。"))
        return self._completed(
            session_id,
            events,
            {
                "operation": operation.model_dump(by_alias=True),
                "preview": preview,
                "validationErrors": preview["validationErrors"],
                "warnings": [],
            },
        )

    def _preview_current_article_edit(
        self,
        session_id: str,
        payload: EditorAgentRunRequestDTO,
        events: list[AgentEventDTO],
    ) -> AgentRunResponseDTO:
        article = self._get_article(payload.article_path)
        operation = self._require_operation(payload)
        preview = preview_current_article_edit(
            body=article.body,
            frontmatter=article.frontmatter,
            operation=operation,
            current_hash=article.version,
        )
        events.append(self._event("tool_result", "已生成编辑预览。", {"riskFlags": preview["riskFlags"]}))
        events.append(self._event("done", "编辑预览已完成。"))
        return self._completed(session_id, events, {"operation": operation.model_dump(by_alias=True), "preview": preview})

    def _write_current_article(
        self,
        session_id: str,
        payload: EditorAgentRunRequestDTO,
        events: list[AgentEventDTO],
    ) -> AgentRunResponseDTO:
        article = self._get_article(payload.article_path)
        operation = self._require_operation(payload)
        tool_result = write_current_article(
            article_service=self.article_service,
            article=article,
            operation=operation,
            expected_content_hash=payload.expected_content_hash,
            approval_mode=payload.approval_mode,
            confirmed=payload.confirmed,
        )
        if tool_result["status"] == "waiting_approval":
            # 高风险或强制审批模式下只保存恢复上下文，不在当前请求里修改文章文件。
            approval = self._store_approval(session_id, payload)
            events.append(self._event("approval_required", "当前编辑需要确认后才能写入。", {"approval": approval}))
            return AgentRunResponseDTO(
                session_id=session_id,
                agent_type="editor",
                status="waiting_approval",
                events=events,
                result={"approval": approval, "preview": tool_result["preview"]},
            )

        events.append(
            self._event(
                "tool_result",
                "文章已写入。",
                {"articleId": tool_result["articleId"], "version": tool_result["latestContentHash"]},
            )
        )
        events.append(self._event("done", "编辑器 Agent 写入完成。"))
        return self._completed(session_id, events, {key: value for key, value in tool_result.items() if key != "status"})

    def _store_approval(self, session_id: str, payload: EditorAgentRunRequestDTO) -> dict[str, str]:
        approval_id = f"approval-{uuid4().hex}"
        # payloadHash 返回给前端并在 resume 时回传，用于确认审批对象没有被替换。
        payload_hash = stable_hash(payload.model_dump_json(by_alias=True))
        self._approvals[approval_id] = PendingApproval(
            session_id=session_id,
            approval_id=approval_id,
            payload_hash=payload_hash,
            request=payload.model_copy(update={"session_id": session_id}),
        )
        return {"sessionId": session_id, "approvalId": approval_id, "payloadHash": payload_hash}

    @staticmethod
    def _build_plan_messages(
        payload: EditorAgentRunRequestDTO,
        frontmatter: dict[str, Any],
        body: str,
    ) -> list[dict[str, str]]:
        selection_text = payload.selection.text if payload.selection else ""
        # 明确约束枚举值，降低不同模型把前端概念翻译成近义词导致校验失败的概率。
        system = (
            "你是博客编辑器文章 Agent。只能返回严格 JSON，不要返回 Markdown。"
            "根据用户指令生成一个 operation 对象，结构为："
            "{type, scope, summary, oldText, newText, insertPosition, frontMatterPatch, riskFlags, confidence}。"
            "type 只能是 insert, replace, delete, rewrite, frontmatter；不要返回 noop。"
            "scope 只能是 document, selection, frontmatter；不要返回 full。"
            "insertPosition 只能是 append, prepend, before_old_text, after_old_text；不要返回 end。"
            "低风险局部修改优先使用 replace selection 或 insert。"
            "不要声称已经写入文件。"
        )
        user = json.dumps(
            {
                "userInput": payload.user_input,
                "approvalMode": payload.approval_mode,
                "selection": selection_text,
                "frontmatter": frontmatter,
                "body": body,
            },
            ensure_ascii=False,
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _run_langchain_agent_plan(
        self,
        payload: EditorAgentRunRequestDTO,
        runtime: EditorArticleToolRuntime,
    ) -> Any | None:
        if self.agent_runner is None:
            return None
        return self.agent_runner.plan_current_article_edit(payload=payload, runtime=runtime)

    def _generate_operation_with_tool_call(
        self,
        payload: EditorAgentRunRequestDTO,
        frontmatter: dict[str, Any],
        body: str,
    ) -> dict[str, Any]:
        messages = self._build_plan_messages(payload, frontmatter, body)
        tool_name = "propose_article_edit"
        if hasattr(self.llm_adapter, "generate_tool_call"):
            tool_result = self.llm_adapter.generate_tool_call(  # type: ignore[attr-defined]
                model_config_id=payload.model_config_id,
                messages=messages,
                tools=[editor_operation_tool_schema(tool_name)],
                tool_name=tool_name,
            )
            arguments = tool_result.get("arguments", {})
            if isinstance(arguments, dict) and isinstance(arguments.get("operation"), dict):
                return arguments["operation"]
            if isinstance(arguments, dict):
                return arguments

        # 少数 OpenAI-compatible 服务不支持强制 tool_choice，最终退回 JSON object 响应。
        llm_result = self.llm_adapter.generate_json(
            model_config_id=payload.model_config_id,
            messages=messages,
        )
        operation_data = llm_result.get("operation", llm_result)
        return operation_data if isinstance(operation_data, dict) else {"type": operation_data}

    def _get_article(self, article_id: str | None):
        if not article_id:
            raise BadRequestError("缺少 articlePath。", code="agent_article_required")
        return self.article_service.get_article(article_id)

    @staticmethod
    def _require_operation(payload: EditorAgentRunRequestDTO) -> EditorAgentOperationDTO:
        if payload.operation is None:
            raise BadRequestError("缺少编辑操作。", code="agent_operation_required")
        return payload.operation

    @staticmethod
    def _event(event_type: str, message: str, data: dict[str, Any] | None = None) -> AgentEventDTO:
        return AgentEventDTO(type=event_type, message=message, data=data)

    @staticmethod
    def _completed(session_id: str, events: list[AgentEventDTO], result: dict[str, Any]) -> AgentRunResponseDTO:
        return AgentRunResponseDTO(session_id=session_id, agent_type="editor", status="completed", events=events, result=result)

    @staticmethod
    def _new_session_id() -> str:
        return f"editor-{uuid4().hex}"
