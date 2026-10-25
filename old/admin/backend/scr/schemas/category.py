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


class CategoryCreateDTO(BaseModel):
    """创建分类请求 DTO。"""

    type: ArticleType
    path: list[str] = Field(min_length=1)
    label: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    cover: str | None = Field(default=None, max_length=300)

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: list[str]) -> list[str]:
        normalized = [segment.strip() for segment in value if segment.strip()]
        if not normalized:
            raise ValueError("path 不能为空")
        return normalized

    @field_validator("label", "description", "cover")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None


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


class CategoryRenameDTO(BaseModel):
    """重命名分类路径请求 DTO。"""

    target_slug: str = Field(min_length=1, max_length=120)
    target_label: str | None = Field(default=None, min_length=1, max_length=120)
    replace_links: bool = True
    dry_run: bool = True
    confirm: bool = False

    @field_validator("target_slug")
    @classmethod
    def validate_target_slug(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("target_slug 不能为空")
        return normalized

    @field_validator("target_label")
    @classmethod
    def normalize_target_label(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None
