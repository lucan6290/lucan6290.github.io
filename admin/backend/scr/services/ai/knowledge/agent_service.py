"""Knowledge Agent orchestration placeholder."""

from __future__ import annotations

from uuid import uuid4

from scr.schemas.agent import AgentEventDTO, AgentRunRequestDTO, AgentRunResponseDTO


class KnowledgeAgentService:
    """Reserved service boundary for the knowledge Agent."""

    def run(self, payload: AgentRunRequestDTO) -> AgentRunResponseDTO:
        session_id = payload.session_id or f"knowledge-{uuid4().hex}"
        # 知识库 Agent 暂不落盘也不检索外部数据，只返回稳定占位响应保证接口契约不漂移。
        return AgentRunResponseDTO(
            session_id=session_id,
            agent_type="knowledge",
            status="failed",
            events=[
                AgentEventDTO(type="session", message="知识库 Agent 会话已开始。", data={"sessionId": session_id}),
                AgentEventDTO(type="done", message="知识库 Agent 尚未实现。"),
            ],
            result={"code": "agent_not_implemented", "command": payload.command},
        )
