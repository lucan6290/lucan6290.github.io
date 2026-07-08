"""Article validation use cases."""

from __future__ import annotations

from scr.core.exceptions import NotFoundError
from scr.schemas.article import ArticleValidationResultDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_image_reference_service import ArticleImageReferenceService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleValidationService:
    """Validate article front matter, sidebars, and local image references."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        sidebar: SidebarService,
        summary: ArticleSummaryService,
        blog_authors: BlogAuthorService,
        article_ids: ArticleIdService,
        image_references: ArticleImageReferenceService,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.sidebar = sidebar
        self.summary = summary
        self.blog_authors = blog_authors
        self.article_ids = article_ids
        self.image_references = image_references

    def validate_article(self, article_id: str) -> ArticleValidationResultDTO:
        article_type, relative_path = self.article_ids.decode(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
        summary = self.summary.build_summary(
            path=path,
            article_type=article_type,
            registered_doc_ids=self.sidebar.list_registered_doc_ids(),
            blog_authors=self.blog_authors.load_authors(),
            parsed=parsed,
        )
        issues = [*summary.issues, *self.image_references.validate_references(path, parsed.body)]
        return ArticleValidationResultDTO(article_id=article_id, issues=issues)
