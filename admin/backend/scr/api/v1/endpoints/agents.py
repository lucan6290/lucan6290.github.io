"""AI Agent endpoints."""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_editor_agent_service, get_knowledge_agent_service, get_writing_agent_service
from scr.schemas.agent import AgentRunRequestDTO, AgentRunResponseDTO, ApprovalResumeRequestDTO, EditorAgentRunRequestDTO
from scr.services.ai.editor.agent_service import EditorAgentService
from scr.services.ai.knowledge.agent_service import KnowledgeAgentService
from scr.services.ai.writing.agent_service import WritingAgentService


router = APIRouter(prefix="/agents", tags=["agents"])
approval_router = APIRouter(prefix="/agent-approvals", tags=["agent-approvals"])


@router.post("/editor/runs", response_model=AgentRunResponseDTO, response_model_by_alias=True)
def run_editor_agent(
    payload: EditorAgentRunRequestDTO,
    editor_agent_service: EditorAgentService = Depends(get_editor_agent_service),
) -> AgentRunResponseDTO:
    """运行编辑器文章 Agent。"""
    return editor_agent_service.run(payload)


@router.post("/writing/runs", response_model=AgentRunResponseDTO, response_model_by_alias=True)
def run_writing_agent(
    payload: AgentRunRequestDTO,
    writing_agent_service: WritingAgentService = Depends(get_writing_agent_service),
) -> AgentRunResponseDTO:
    """运行写作 Agent。"""
    return writing_agent_service.run(payload)


@router.post("/knowledge/runs", response_model=AgentRunResponseDTO, response_model_by_alias=True)
def run_knowledge_agent(
    payload: AgentRunRequestDTO,
    knowledge_agent_service: KnowledgeAgentService = Depends(get_knowledge_agent_service),
) -> AgentRunResponseDTO:
    """运行知识库 Agent。"""
    return knowledge_agent_service.run(payload)


@approval_router.post("/{approval_id}/resume", response_model=AgentRunResponseDTO, response_model_by_alias=True)
def resume_agent_approval(
    approval_id: str,
    payload: ApprovalResumeRequestDTO,
    editor_agent_service: EditorAgentService = Depends(get_editor_agent_service),
) -> AgentRunResponseDTO:
    """恢复待审批的 Agent 写入。"""
    # 审批只恢复编辑器写入流程；写作/知识库 Agent 当前没有会修改文件的审批步骤。
    return editor_agent_service.resume_approval(approval_id, payload)
