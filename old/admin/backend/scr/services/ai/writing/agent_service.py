"""Writing Agent orchestration placeholder."""

from __future__ import annotations

from uuid import uuid4

from scr.schemas.agent import AgentEventDTO, AgentRunRequestDTO, AgentRunResponseDTO


class WritingAgentService:
    """Reserved service boundary for the writing Agent."""

    def run(self, payload: AgentRunRequestDTO) -> AgentRunResponseDTO:
        session_id = payload.session_id or f"writing-{uuid4().hex}"
        # 先保持 API 契约可用，前端可以接入统一 Agent 面板，具体写作流程后续在此服务内扩展。
        return AgentRunResponseDTO(
            session_id=session_id,
            agent_type="writing",
            status="failed",
            events=[
                AgentEventDTO(type="session", message="写作 Agent 会话已开始。", data={"sessionId": session_id}),
                AgentEventDTO(type="done", message="写作 Agent 尚未实现。"),
            ],
            result={"code": "agent_not_implemented", "command": payload.command},
        )
