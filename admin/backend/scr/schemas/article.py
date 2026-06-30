"""文章相关的响应数据传输对象（DTO）定义。

本模块中的 DTO 用于在 API 层与 ArticleService 之间传递文章数据，
均基于 Pydantic BaseModel，承担序列化与字段校验职责。
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from scr.models.article import ArticleType


class ValidationIssueDTO(BaseModel):
    """单条文章校验问题，描述 frontmatter 或登记状态上的不规范项。"""

    code: str  # 问题代码，如 docs_title_missing、blog_author_unknown
    message: str  # 人类可读的问题描述
    severity: str = "warning"  # 严重级别：error（阻断）/ warning（建议）


class ArticleSummaryDTO(BaseModel):
    """文章摘要，用于列表展示，包含元信息与校验结果。"""

    id: str  # 文章唯一标识，由 type:relative_path 经 base64 编码生成
    type: ArticleType  # 文章类型：docs / blog
    type_label: str  # 内容类型显示名，如 知识库 / 博客
    title: str | None = None  # 标题，取自 frontmatter.title
    description: str | None = None  # 描述，取自 frontmatter.description
    relative_path: str  # 相对于文章根目录（docs / blog）的 posix 路径
    route: str  # 前端访问路由，如 /docs/xxx 或 /blog/xxx
    slug: str  # URL 友好的标识，docs 取 doc_id，blog 取 frontmatter.slug 或文件名
    tags: list[str] = Field(default_factory=list)  # 标签列表，取自 frontmatter.tags
    authors: list[str] = Field(default_factory=list)  # 作者列表，取自 frontmatter.authors
    category_path: list[str] = Field(default_factory=list)  # 分类层级（仅 docs，按目录拆分）
    category_label: str  # 分类显示名，优先来自 admin/backend/data/content-schema/categories.yml
    sidebar_registered: bool | None = None  # 是否已登记到 sidebars.ts（仅 docs 有值）
    version: str  # 文件版本，用于保存文章时的乐观锁校验
    updated_at: str  # 文件最后修改时间，ISO 8601 字符串
    issues: list[ValidationIssueDTO] = Field(default_factory=list)  # 该文章的校验问题集合


class ArticleListResponseDTO(BaseModel):
    """文章列表分页响应 DTO。"""

    items: list[ArticleSummaryDTO]
    page: int
    page_size: int
    total: int
    has_next: bool


class ArticleValidationResultDTO(BaseModel):
    """单篇文章校验结果 DTO。"""

    article_id: str
    issues: list[ValidationIssueDTO] = Field(default_factory=list)


class ImageDTO(BaseModel):
    """文章图片响应 DTO。"""

    name: str
    relative_path: str
    markdown_url: str
    markdown: str | None = None
    size: int
    referenced: bool | None = None
    created_at: str | None = None


class ArticleImageListDTO(BaseModel):
    """文章图片列表响应 DTO。"""

    article_id: str
    image_dir: str | None = None
    images: list[ImageDTO] = Field(default_factory=list)


class ArticleImageCheckDTO(BaseModel):
    """文章图片引用检查响应 DTO。"""

    article_id: str
    image_dir: str | None = None
    referenced_images: list[str] = Field(default_factory=list)
    unused_images: list[str] = Field(default_factory=list)
    missing_references: list[str] = Field(default_factory=list)
    out_of_scope_references: list[str] = Field(default_factory=list)


class ArticleDetailDTO(ArticleSummaryDTO):
    """文章详情，在摘要基础上扩展正文与原始内容，用于详情页展示与编辑。"""

    frontmatter: dict[str, Any] = Field(default_factory=dict)  # 原始 frontmatter 字典，保留全部字段
    body: str  # 解析后的 markdown 正文（去除 frontmatter）
    raw_content: str  # 文件的原始完整内容（含 frontmatter），用于编辑回显
    image_dir: str | None = None  # 关联的图片目录路径（{文件名}-imgs），不存在则为 None


class ArticleCreateDTO(BaseModel):
    """创建文章的请求 DTO。docs 与 blog 共用基础字段，按 type 执行差异校验。"""

    type: ArticleType
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    body: str = ""

    category_path: list[str] = Field(default_factory=list)
    sidebar_position: int | None = Field(default=None, ge=1)

    authors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    date: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("slug 不能为空。")
        return normalized

    @field_validator("category_path")
    @classmethod
    def validate_category_path(cls, value: list[str]) -> list[str]:
        return [segment.strip() for segment in value if segment.strip()]

    @field_validator("authors", "tags")
    @classmethod
    def normalize_string_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "ArticleCreateDTO":
        if self.type == ArticleType.blog:
            if not self.authors:
                raise ValueError("blog 文章必须填写 authors。")
            if not self.tags:
                raise ValueError("blog 文章必须填写 tags。")
        return self


class ArticleUpdateDTO(BaseModel):
    """保存文章请求 DTO。"""

    frontmatter: dict[str, Any]
    body: str
    validate_after_save: bool = True
    expected_version: str | None = None


class ArticleMoveDTO(BaseModel):
    """移动或重命名文章请求 DTO。"""

    target_type: ArticleType
    target_slug: str = Field(min_length=1, max_length=120)
    target_category_path: list[str] = Field(default_factory=list)
    target_date: str | None = None
    replace_links: bool = False
    dry_run: bool = True
    confirm: bool = False

    @field_validator("target_slug")
    @classmethod
    def validate_target_slug(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("target_slug 不能为空。")
        return normalized

    @field_validator("target_category_path")
    @classmethod
    def validate_target_category_path(cls, value: list[str]) -> list[str]:
        return [segment.strip() for segment in value if segment.strip()]

    @field_validator("target_date")
    @classmethod
    def normalize_target_date(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None
