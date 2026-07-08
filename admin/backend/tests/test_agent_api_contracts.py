from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_editor_agent_service, get_knowledge_agent_service, get_writing_agent_service
from scr.main import app
from scr.schemas.agent import AgentEventDTO, AgentRunRequestDTO, AgentRunResponseDTO, ApprovalResumeRequestDTO, EditorAgentRunRequestDTO


class FakeEditorAgentService:
    def __init__(self) -> None:
        self.payload: EditorAgentRunRequestDTO | None = None
        self.resume_payload: ApprovalResumeRequestDTO | None = None

    def run(self, payload: EditorAgentRunRequestDTO) -> AgentRunResponseDTO:
        self.payload = payload
        return AgentRunResponseDTO(
            sessionId="editor-test",
            agentType="editor",
            status="completed",
            events=[AgentEventDTO(type="done", message="ok")],
            result={"preview": {"beforeHash": "v1"}},
        )

    def resume_approval(self, approval_id: str, payload: ApprovalResumeRequestDTO) -> AgentRunResponseDTO:
        self.resume_payload = payload
        return AgentRunResponseDTO(
            sessionId=payload.session_id,
            agentType="editor",
            status="completed",
            events=[AgentEventDTO(type="done", message=approval_id)],
            result={"saved": True},
        )


class FakeGenericAgentService:
    def __init__(self, agent_type: str) -> None:
        self.agent_type = agent_type
        self.payload: AgentRunRequestDTO | None = None

    def run(self, payload: AgentRunRequestDTO) -> AgentRunResponseDTO:
        self.payload = payload
        return AgentRunResponseDTO(
            sessionId=f"{self.agent_type}-test",
            agentType=self.agent_type,
            status="failed",
            events=[AgentEventDTO(type="done", message="not implemented")],
            result={"code": "agent_not_implemented"},
        )


def test_editor_agent_run_api_uses_camel_case_contract(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeEditorAgentService()
    app.dependency_overrides[get_editor_agent_service] = lambda: fake_service

    response = client.post(
        "/api/v1/agents/editor/runs",
        json={
            "articlePath": "docs:test.md",
            "approvalMode": "delegate-approval",
            "command": "plan_current_article_edit",
            "userInput": "润色一下",
            "modelConfigId": "deepseek-v4-pro-default",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["sessionId"] == "editor-test"
    assert response.json()["agentType"] == "editor"
    assert fake_service.payload is not None
    assert fake_service.payload.article_path == "docs:test.md"
    assert fake_service.payload.model_config_id == "deepseek-v4-pro-default"


def test_agent_approval_resume_api_uses_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeEditorAgentService()
    app.dependency_overrides[get_editor_agent_service] = lambda: fake_service

    response = client.post(
        "/api/v1/agent-approvals/approval-1/resume",
        json={
            "sessionId": "editor-test",
            "approvalId": "approval-1",
            "payloadHash": "hash",
            "approved": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["result"] == {"saved": True}
    assert fake_service.resume_payload is not None
    assert fake_service.resume_payload.payload_hash == "hash"


def test_writing_agent_run_api_is_reserved(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeGenericAgentService("writing")
    app.dependency_overrides[get_writing_agent_service] = lambda: fake_service

    response = client.post(
        "/api/v1/agents/writing/runs",
        json={
            "approvalMode": "delegate-approval",
            "command": "draft",
            "userInput": "写一篇博客大纲",
            "modelConfigId": "deepseek-v4-pro-default",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["agentType"] == "writing"
    assert fake_service.payload is not None
    assert fake_service.payload.command == "draft"


def test_knowledge_agent_run_api_is_reserved(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeGenericAgentService("knowledge")
    app.dependency_overrides[get_knowledge_agent_service] = lambda: fake_service

    response = client.post(
        "/api/v1/agents/knowledge/runs",
        json={
            "approvalMode": "delegate-approval",
            "command": "answer",
            "userInput": "查一下这篇文章关联了哪些资料",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["agentType"] == "knowledge"
    assert fake_service.payload is not None
    assert fake_service.payload.command == "answer"
