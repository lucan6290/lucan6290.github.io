from scr.models.article import ArticleType
from scr.schemas.agent import ApprovalResumeRequestDTO, EditorAgentOperationDTO, EditorAgentRunRequestDTO
from scr.schemas.article import ArticleDetailDTO, ArticleUpdateDTO
from scr.services.ai.editor.agent_service import EditorAgentService
from scr.services.ai.editor.langchain_agent import EditorAgentPlanResult


def _article(body: str = "旧段落") -> ArticleDetailDTO:
    return ArticleDetailDTO(
        id="docs:test.md",
        type=ArticleType.docs,
        type_label="docs",
        title="Test Article",
        description=None,
        date=None,
        last_update=None,
        relative_path="test.md",
        route="/docs/test",
        slug="test",
        tags=[],
        authors=[],
        category_path=[],
        category_label="docs",
        sidebar_registered=True,
        version="v1",
        updated_at="2026-07-04T00:00:00+08:00",
        issues=[],
        frontmatter={"title": "Test Article"},
        body=body,
        raw_content=f"---\ntitle: Test Article\n---\n{body}",
    )


class FakeArticleService:
    def __init__(self) -> None:
        self.detail = _article()
        self.saved_payload: ArticleUpdateDTO | None = None

    def get_article(self, article_id: str) -> ArticleDetailDTO:
        assert article_id == self.detail.id
        return self.detail

    def save_article(self, article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
        assert article_id == self.detail.id
        self.saved_payload = payload
        self.detail = _article(payload.body)
        self.detail.version = "v2"
        self.detail.frontmatter = payload.frontmatter
        return self.detail


class FakeLLMAdapter:
    def generate_json(self, **_: object) -> dict[str, object]:
        return {
            "operation": {
                "type": "replace",
                "scope": "selection",
                "summary": "润色选区",
                "oldText": "旧段落",
                "newText": "新段落",
                "riskFlags": [],
                "confidence": 0.9,
            }
        }


class ToolCallLLMAdapter:
    def __init__(self) -> None:
        self.used_tool_call = False

    def generate_tool_call(self, **kwargs: object) -> dict[str, object]:
        self.used_tool_call = True
        assert kwargs["tool_name"] == "propose_article_edit"
        tools = kwargs["tools"]
        assert isinstance(tools, list)
        assert tools[0]["function"]["name"] == "propose_article_edit"
        return {
            "name": "propose_article_edit",
            "arguments": {
                "type": "replace",
                "scope": "selection",
                "summary": "润色选区",
                "oldText": "旧段落",
                "newText": "新段落",
                "riskFlags": [],
                "confidence": 0.9,
            },
        }

    def generate_json(self, **_: object) -> dict[str, object]:
        raise AssertionError("tool calling should be preferred")


class FakeLangChainAgentRunner:
    def __init__(self) -> None:
        self.read_result: dict[str, object] | None = None

    def plan_current_article_edit(self, *, payload: EditorAgentRunRequestDTO, runtime: object) -> EditorAgentPlanResult:
        assert payload.command == "plan_current_article_edit"
        self.read_result = runtime.read_current_article()
        preview_result = runtime.preview_current_article_edit(
            {
                "type": "replace",
                "scope": "selection",
                "summary": "润色选区",
                "oldText": "旧段落",
                "newText": "新段落",
                "riskFlags": [],
                "confidence": 0.9,
            }
        )
        return EditorAgentPlanResult(
            operation_data=preview_result["operation"],
            preview=preview_result["preview"],
            tool_events=[
                {"tool": "read_current_article", "args": {}, "result": self.read_result},
                {"tool": "preview_current_article_edit", "args": {"operation": preview_result["operation"]}, "result": preview_result},
            ],
        )


class BadOldTextLLMAdapter:
    def generate_json(self, **_: object) -> dict[str, object]:
        return {
            "operation": {
                "type": "replace",
                "scope": "selection",
                "summary": "润色选区",
                "oldText": "模型抄错的原文",
                "newText": "新段落",
                "riskFlags": [],
                "confidence": 0.8,
            }
        }


class InvalidLLMAdapter:
    def generate_json(self, **_: object) -> dict[str, object]:
        return {
            "operation": {
                "type": "replace",
                "scope": "selection",
                "summary": "润色选区",
                "oldText": "不存在的原文",
                "newText": "新段落",
                "riskFlags": [],
                "confidence": 0.8,
            }
        }


class CoercibleLLMAdapter:
    def generate_json(self, **_: object) -> dict[str, object]:
        return {
            "operation": {
                "type": "add",
                "scope": "full",
                "summary": "补充内容",
                "newText": "新段落",
                "insertPosition": "end",
                "riskFlags": [],
                "confidence": 0.8,
            }
        }


class NoopLLMAdapter:
    def generate_json(self, **_: object) -> dict[str, object]:
        return {
            "operation": {
                "type": "noop",
                "scope": "full",
                "summary": "无需修改",
                "riskFlags": [],
                "confidence": 0.8,
            }
        }


def test_editor_agent_plan_returns_operation_and_preview() -> None:
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=FakeLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="润色选区",
            modelConfigId="test-model",
        )
    )

    assert response.status == "completed"
    assert response.result is not None
    assert response.result["operation"]["newText"] == "新段落"
    assert "新段落" in response.result["preview"]["diff"]


def test_editor_agent_plan_prefers_llm_tool_calling() -> None:
    llm_adapter = ToolCallLLMAdapter()
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=llm_adapter)  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="润色选区",
            modelConfigId="test-model",
        )
    )

    assert llm_adapter.used_tool_call is True
    assert response.status == "completed"
    assert response.result is not None
    assert response.result["operation"]["newText"] == "新段落"


def test_editor_agent_plan_uses_agent_runner_tool_loop_when_configured() -> None:
    agent_runner = FakeLangChainAgentRunner()
    service = EditorAgentService(
        article_service=FakeArticleService(),
        llm_adapter=FakeLLMAdapter(),  # type: ignore[arg-type]
        agent_runner=agent_runner,
    )

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="润色选区",
            modelConfigId="test-model",
        )
    )

    assert agent_runner.read_result is not None
    assert response.status == "completed"
    assert response.result is not None
    assert response.result["operation"]["newText"] == "新段落"
    assert [event.message for event in response.events if event.type == "tool_call"][-2:] == [
        "Agent 调用了工具：read_current_article。",
        "Agent 调用了工具：preview_current_article_edit。",
    ]


def test_editor_agent_plan_uses_selection_when_model_old_text_is_wrong() -> None:
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=BadOldTextLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="润色选区",
            modelConfigId="test-model",
            selection={"text": "旧段落"},
        )
    )

    assert response.status == "completed"
    assert response.result is not None
    assert response.result["operation"]["oldText"] == "旧段落"
    assert response.result["validationErrors"] == []


def test_editor_agent_plan_fails_when_preview_is_invalid() -> None:
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=InvalidLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="润色选区",
            modelConfigId="test-model",
        )
    )

    assert response.status == "failed"
    assert response.result is not None
    assert response.result["validationErrors"] == ["未找到 oldText，无法替换。"]


def test_editor_agent_plan_coerces_common_model_enum_aliases() -> None:
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=CoercibleLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="在末尾补充内容",
            modelConfigId="test-model",
        )
    )

    assert response.status == "completed"
    assert response.result is not None
    assert response.result["operation"]["type"] == "insert"
    assert response.result["operation"]["scope"] == "document"
    assert response.result["operation"]["insertPosition"] == "append"


def test_editor_agent_plan_returns_failed_for_invalid_model_operation_schema() -> None:
    service = EditorAgentService(article_service=FakeArticleService(), llm_adapter=NoopLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="plan_current_article_edit",
            userInput="看看是否需要修改",
            modelConfigId="test-model",
        )
    )

    assert response.status == "failed"
    assert response.result is not None
    assert response.result["validationErrors"] == ["type 字段不合法：'noop'。"]


def test_editor_agent_delegate_approval_writes_low_risk_operation() -> None:
    article_service = FakeArticleService()
    service = EditorAgentService(article_service=article_service, llm_adapter=FakeLLMAdapter())  # type: ignore[arg-type]

    response = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="delegate-approval",
            command="write_current_article",
            expectedContentHash="v1",
            operation=EditorAgentOperationDTO(
                type="replace",
                scope="selection",
                summary="润色选区",
                oldText="旧段落",
                newText="新段落",
            ),
        )
    )

    assert response.status == "completed"
    assert article_service.saved_payload is not None
    assert article_service.saved_payload.body == "新段落"


def test_editor_agent_request_approval_waits_and_resumes() -> None:
    article_service = FakeArticleService()
    service = EditorAgentService(article_service=article_service, llm_adapter=FakeLLMAdapter())  # type: ignore[arg-type]

    waiting = service.run(
        EditorAgentRunRequestDTO(
            articlePath="docs:test.md",
            approvalMode="request-approval",
            command="write_current_article",
            expectedContentHash="v1",
            operation=EditorAgentOperationDTO(
                type="replace",
                scope="selection",
                summary="润色选区",
                oldText="旧段落",
                newText="新段落",
            ),
        )
    )

    assert waiting.status == "waiting_approval"
    approval = waiting.result["approval"]  # type: ignore[index]

    resumed = service.resume_approval(
        approval["approvalId"],
        ApprovalResumeRequestDTO(
            sessionId=approval["sessionId"],
            approvalId=approval["approvalId"],
            payloadHash=approval["payloadHash"],
            approved=True,
        ),
    )

    assert resumed.status == "completed"
    assert article_service.saved_payload is not None
    assert article_service.saved_payload.body == "新段落"
