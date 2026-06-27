"""Structured schemas for AI writing workflows."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AIApprovalMode(str, Enum):
    REQUEST_APPROVAL = "request-approval"
    DELEGATE_APPROVAL = "delegate-approval"
    FULL_ACCESS = "full-access"


class AIWritingGoal(str, Enum):
    AUTO = "auto"
    BLOG_DRAFT = "blog-draft"
    STUDY_NOTE = "study-note"
    PITFALL_REVIEW = "pitfall-review"
    PROJECT_LOG = "project-log"
    THOUGHT_ESSAY = "thought-essay"
    RESOURCE_DIGEST = "resource-digest"
    OUTLINE_EXPANSION = "outline-expansion"


class AIModelConfig(BaseModel):
    baseUrl: str = ""
    apiKey: str = ""
    modelId: str = ""
    provider: str = "custom"
    apiFormat: Literal["openai", "anthropic"] = "openai"
    anthropicBaseUrl: str = ""
    thinkingMode: Literal["enabled", "disabled"] = "disabled"
    reasoningEffort: Literal["high", "max"] = "high"
    agentMode: bool = False
    toolCalls: bool = False
    strictToolCalls: bool = False
    jsonMode: bool = False
    temperature: float = 0.3
    maxTokens: int = 4096


class CategoryRegistryItem(BaseModel):
    frontend_name1: str = ""
    category_slug: str = ""
    note_prefix1: str = ""
    prefix1: str
    primaryName: str
    primarySlug: str
    dir: str
    cover: str
    sort_order: int = 0
    enabled: bool = True
    children: list[dict[str, Any]] = Field(default_factory=list)


class AIDraftPlan(BaseModel):
    schemaVersion: str = "1.0"
    approvalMode: AIApprovalMode
    writingGoal: AIWritingGoal
    userIntent: str
    inputType: str
    clarificationRequired: bool = False
    clarificationQuestions: list[str] = Field(default_factory=list, max_length=3)
    primarySlug: str
    primaryName: str
    prefix1: str
    prefix2: str
    title: str
    tags: list[str] = Field(default_factory=list)
    description: str
    outline: list[str] = Field(default_factory=list)
    imagePlaceholders: list[str] = Field(default_factory=list)
    bodyMarkdown: str
    missingInfoQuestions: list[str] = Field(default_factory=list)
    riskFlags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reviewChecklist: list[str] = Field(default_factory=list)
    rationale: str = ""


class AgentPlanRequest(BaseModel):
    sessionId: str | None = None
    userInput: str
    approvalMode: AIApprovalMode = AIApprovalMode.REQUEST_APPROVAL
    writingGoal: AIWritingGoal = AIWritingGoal.AUTO
    userPreferences: dict[str, Any] = Field(default_factory=dict)
    clarificationAnswers: list[str] = Field(default_factory=list)
    conversationHistory: list[dict[str, str]] = Field(default_factory=list)
    model: AIModelConfig


class AgentCommitRequest(BaseModel):
    sessionId: str
    approvalMode: AIApprovalMode = AIApprovalMode.REQUEST_APPROVAL
    confirmed: bool = False
    idempotencyKey: str
    plan: AIDraftPlan


class AIEditOperation(BaseModel):
    type: Literal["insert", "replace", "delete", "rewrite", "frontmatter"]
    scope: Literal["selection", "cursor", "document", "frontmatter"]
    approvalMode: AIApprovalMode
    requiresManualApproval: bool = True
    summary: str
    oldText: str | None = None
    newText: str | None = None
    frontMatterPatch: dict[str, Any] | None = None
    riskFlags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1, ge=0, le=1)


class SelectionRange(BaseModel):
    text: str = ""
    startLine: int | None = None
    endLine: int | None = None


class EditPlanRequest(BaseModel):
    sessionId: str | None = None
    articlePath: str
    instruction: str
    approvalMode: AIApprovalMode = AIApprovalMode.REQUEST_APPROVAL
    scope: Literal["selection", "cursor", "document", "frontmatter"] = "document"
    selection: SelectionRange | None = None
    model: AIModelConfig


class EditApplyRequest(BaseModel):
    sessionId: str
    articlePath: str
    approvalMode: AIApprovalMode = AIApprovalMode.REQUEST_APPROVAL
    confirmed: bool = False
    operation: AIEditOperation


class ArticleIndexItem(BaseModel):
    path: str
    fileName: str
    title: str
    date: str | None = None
    updated: str | None = None
    categories: list[list[str]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: Literal["draft", "wip", "published"] | None = None
    published: bool | None = None
    description: str | None = None
    headings: list[str] = Field(default_factory=list)
    excerpt: str = ""
    mtime: str
    contentHash: str
    warnings: list[str] = Field(default_factory=list)


class ArticleChunk(BaseModel):
    id: str
    articlePath: str
    articleTitle: str
    headingPath: list[str] = Field(default_factory=list)
    text: str
    startLine: int | None = None
    endLine: int | None = None
    contentHash: str


class ArticleIndexScanRequest(BaseModel):
    includeDrafts: bool = True
    force: bool = False


class KnowledgeQARequest(BaseModel):
    sessionId: str | None = None
    question: str
    forceRescan: bool = False
    includeDrafts: bool = True
    model: AIModelConfig | None = None


class KnowledgeCitation(BaseModel):
    title: str
    path: str
    headingPath: list[str] = Field(default_factory=list)
    lines: list[int] | None = None
