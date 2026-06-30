"""分类相关 DTO。"""

from pydantic import BaseModel, Field, field_validator

from scr.models.article import ArticleType


class CategoryDTO(BaseModel):
    """分类树节点响应 DTO。"""

    id: str
    type: ArticleType
    slug: str
    label: str
    path: list[str]
    description: str | None = None
    cover: str | None = None
    sort_order: int | None = None
    enabled: bool = True
    article_count: int | None = None
    children: list["CategoryDTO"] = Field(default_factory=list)


class CategoryUpdateDTO(BaseModel):
    """更新分类注册表请求 DTO。"""

    label: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    cover: str | None = Field(default=None, max_length=300)

    @field_validator("label", "description", "cover")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None
