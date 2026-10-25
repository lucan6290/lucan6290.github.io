"""站点内容校验相关 DTO。"""

from pydantic import BaseModel, Field

from scr.models.article import ArticleType
from scr.schemas.article import ValidationIssueDTO


class SiteValidationRequestDTO(BaseModel):
    """全站内容校验请求 DTO。"""

    type: ArticleType | None = None
    include_warnings: bool = True
    only_with_issues: bool = True


class ArticleValidationSummaryDTO(BaseModel):
    """全站校验中的单篇文章结果。"""

    article_id: str
    type: ArticleType
    relative_path: str
    issues: list[ValidationIssueDTO] = Field(default_factory=list)


class SiteValidationResultDTO(BaseModel):
    """全站内容校验响应 DTO。"""

    type: ArticleType | None = None
    checked_count: int
    article_count: int
    issue_count: int
    error_count: int
    warning_count: int
    articles: list[ArticleValidationSummaryDTO] = Field(default_factory=list)
