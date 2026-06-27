from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class PostStatus(str, Enum):
    DRAFT = "draft"
    WIP = "wip"
    PUBLISHED = "published"


class FrontMatter(BaseModel):
    title: str = ""
    date: str = ""
    updated: str | None = None
    categories: list[Any] | None = None
    tags: list[str] | None = None
    description: str | None = None
    layout: str | None = None
    comments: bool | None = None
    permalink: str | None = None
    excerpt: str | None = None
    published: bool | None = None
    lang: str | None = None
    cover: str | None = None
    sticky: int | None = None
    slug: str | None = None
    status: PostStatus | None = None
    series: str | None = None
    series_order: int | None = None


class PostInfo(BaseModel):
    title: str = ""
    path: str = ""
    date: str = ""
    updated: str | None = None
    categories: list[str] = []
    tags: list[str] = []
    description: str | None = None
    cover: str | None = None
    status: PostStatus = PostStatus.PUBLISHED
    series: str | None = None
    seriesOrder: int | None = None


class PostDetail(BaseModel):
    frontMatter: dict[str, Any] | None = None
    content: str | None = None
    raw: str | None = None


class CreatePostRequest(BaseModel):
    title: str
    prefix1: str
    prefix2: str


class UpdatePostRequest(BaseModel):
    frontMatter: dict[str, Any] | None = None
    content: str | None = None


class UploadImageRequest(BaseModel):
    articlePath: str
    imageData: str
    extension: str


class AssetUsageRequest(BaseModel):
    articlePath: str
    content: str | None = None


class ImageInfo(BaseModel):
    name: str
    path: str
    url: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    baseUrl: str = ""
    apiKey: str = ""
    modelId: str = ""
    stream: bool = True
    provider: str = "custom"
    apiFormat: str = "openai"
    anthropicBaseUrl: str = ""
    thinkingMode: str = "disabled"
    reasoningEffort: str = "high"
    agentMode: bool = False
    toolCalls: bool = False
    strictToolCalls: bool = False
    jsonMode: bool = False
    temperature: float = 0.7
    maxTokens: int = 4096


class TestConnectionRequest(BaseModel):
    baseUrl: str
    apiKey: str
    modelId: str
    provider: str = "custom"
    apiFormat: str = "openai"
    anthropicBaseUrl: str = ""
    thinkingMode: str = "disabled"
    reasoningEffort: str = "high"
    agentMode: bool = False
    toolCalls: bool = False
    strictToolCalls: bool = False
    jsonMode: bool = False
    temperature: float = 0.3
    maxTokens: int = 4096


class ModelPreset(BaseModel):
    id: str
    name: str
    baseUrl: str
    modelId: str
    provider: str = "custom"
    apiFormat: str = "openai"
    anthropicBaseUrl: str = ""
    thinkingMode: str = "disabled"
    reasoningEffort: str = "high"
    agentMode: bool = False
    toolCalls: bool = False
    strictToolCalls: bool = False
    jsonMode: bool = False
    temperature: float = 0.3
    maxTokens: int = 4096
