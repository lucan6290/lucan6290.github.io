"""Article detail reading service."""

from __future__ import annotations

from pathlib import Path

from scr.core.exceptions import NotFoundError
from scr.schemas.article import ArticleDetailDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleDetailService:
    """Read a full article detail from disk."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        sidebar: SidebarService,
        summary: ArticleSummaryService,
        blog_authors: BlogAuthorService,
        article_ids: ArticleIdService,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.sidebar = sidebar
        self.summary = summary
        self.blog_authors = blog_authors
        self.article_ids = article_ids

    def get_article(self, article_id: str) -> ArticleDetailDTO:
        article_type, relative_path = self.article_ids.decode(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        summary = self.summary.build_summary(
            path=path,
            article_type=article_type,
            registered_doc_ids=self.sidebar.list_registered_doc_ids(),
            blog_authors=self.blog_authors.load_authors(),
            parsed=parsed,
        )

        image_dir = self.image_dir_for(path)
        return ArticleDetailDTO(
            **summary.model_dump(),
            frontmatter=parsed.frontmatter,
            body=parsed.body,
            raw_content=parsed.raw_content,
            image_dir=image_dir.as_posix() if image_dir.exists() else None,
        )

    @staticmethod
    def image_dir_for(path: Path) -> Path:
        return path.with_name(f"{path.stem}-imgs")
