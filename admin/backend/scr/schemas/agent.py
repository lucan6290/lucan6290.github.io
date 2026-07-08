"""AI Agent DTOs."""

from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        protected_namespaces=(),
    )


AIApprovalMode: TypeAlias = Literal["request-approval", "delegate-approval", "full-access"]
AgentType: TypeAlias = Literal["editor", "writing", "knowledge"]
AgentStatus: TypeAlias = Literal["completed", "failed", "waiting_approval"]
AgentEventType: TypeAlias = Literal["session", "message", "tool_call", "tool_result", "approval_required", "error", "done"]


class AgentEventDTO(CamelModel):
    type: AgentEventType
    message: str
    data: dict[str, Any] | None = None
    tool_call_id: str | None = None


class AgentRunResponseDTO(CamelModel):
    session_id: str
    agent_type: AgentType
    status: AgentStatus
    events: list[AgentEventDTO] = Field(default_factory=list)
    result: dict[str, Any] | None = None


class AgentRunRequestDTO(CamelModel):
    session_id: str | None = None
    user_input: str | None = None
    approval_mode: AIApprovalMode
    model_config_id: str | None = None
    context: dict[str, Any] | None = None
    command: str


class EditorSelectionDTO(CamelModel):
    text: str
    start_offset: int | None = None
    end_offset: int | None = None
    start_line: int | None = None
    end_line: int | None = None


class EditorAgentOperationDTO(CamelModel):
    type: Literal["insert", "replace", "delete", "rewrite", "frontmatter"]
    scope: Literal["document", "selection", "frontmatter"]
    summary: str = ""
    old_text: str | None = None
    new_text: str | None = None
    insert_position: Literal["append", "prepend", "before_old_text", "after_old_text"] | None = None
    front_matter_patch: dict[str, Any] | None = None
    risk_flags: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class EditorAgentRunRequestDTO(CamelModel):
    session_id: str | None = None
    user_input: str | None = None
    approval_mode: AIApprovalMode
    confirmed: bool = False
    model_config_id: str | None = None
    context: dict[str, Any] | None = None
    article_path: str | None = None
    selection: EditorSelectionDTO | None = None
    command: Literal[
        "plan_current_article_edit",
        "read_current_article",
        "get_current_selection",
        "preview_current_article_edit",
        "write_current_article",
    ]
    operation: EditorAgentOperationDTO | None = None
    expected_content_hash: str | None = None


class ApprovalResumeRequestDTO(CamelModel):
    session_id: str
    approval_id: str
    payload_hash: str
    approved: bool


class AIModelConfigDTO(CamelModel):
    id: str
    name: str
    provider: str = "custom"
    base_url: str
    model_id: str
    api_format: Literal["openai", "anthropic"] = "openai"
    temperature: float = 0.3
    max_tokens: int = 4096
    thinking_mode: Literal["enabled", "disabled"] = "disabled"
    reasoning_effort: Literal["high", "max"] = "high"
    is_default: bool = False


class AIModelConfigCreateDTO(AIModelConfigDTO):
    api_key: str = ""


class AIModelConfigInternalDTO(AIModelConfigCreateDTO):
    pass
