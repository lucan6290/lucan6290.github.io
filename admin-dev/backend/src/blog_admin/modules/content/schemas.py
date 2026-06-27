from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class PostStatus(str, Enum):
    DRAFT = "draft"
    WIP = "wip"
    PUBLISHED = "published"


class CreatePostRequest(BaseModel):
    title: str
    prefix1: str
    prefix2: str


class UpdatePostRequest(BaseModel):
    frontMatter: dict[str, Any] | None = None
    content: str | None = None
