from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AIApprovalMode(str, Enum):
    REQUEST_APPROVAL = "request-approval"
    DELEGATE_APPROVAL = "delegate-approval"
    FULL_ACCESS = "full-access"


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


JsonDict = dict[str, Any]
