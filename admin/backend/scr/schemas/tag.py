"""标签相关 DTO。"""

from pydantic import BaseModel, Field


class TagDTO(BaseModel):
    """标签响应 DTO。"""

    slug: str
    label: str
    description: str | None = None
    usage_count: int = 0


class TagCreateDTO(BaseModel):
    """创建标签请求 DTO。"""

    label: str = Field(min_length=1, max_length=80)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)


class TagSyncResultDTO(BaseModel):
    """标签同步结果 DTO。"""

    dry_run: bool
    requires_confirmation: bool
    discovered_count: int
    existing_count: int
    created_tags: list[TagDTO] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
