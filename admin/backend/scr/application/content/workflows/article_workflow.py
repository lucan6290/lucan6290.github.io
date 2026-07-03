"""Article workflow dispatcher."""

from typing import Protocol

from scr.application.content.workflows.blog_article_workflow import BlogArticleWorkflow
from scr.application.content.workflows.docs_article_workflow import DocsArticleWorkflow
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO


class ArticleCreateWorkflow(Protocol):
    """Workflow contract for creating one article type."""

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """Create an article and return its detail DTO."""


class ArticleWorkflowService:
    """Dispatch article mutations to docs/blog workflow implementations."""

    def __init__(
        self,
        _legacy_article_service: object | None = None,
        *,
        docs_workflow: ArticleCreateWorkflow | None = None,
        blog_workflow: ArticleCreateWorkflow | None = None,
    ) -> None:
        self.docs = docs_workflow or DocsArticleWorkflow()
        self.blog = blog_workflow or BlogArticleWorkflow()

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        if payload.type == ArticleType.docs:
            return self.docs.create_article(payload)
        if payload.type == ArticleType.blog:
            return self.blog.create_article(payload)
        raise ValueError(f"Unsupported article type: {payload.type}")
