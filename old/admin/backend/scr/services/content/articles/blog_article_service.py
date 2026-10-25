"""Blog article file operations."""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from scr.core.exceptions import ConflictError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


class BlogArticleService:
    """Create blog article files without orchestrating derived indexes."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        markdown: MarkdownService | None = None,
        blog_authors: BlogAuthorService | None = None,
        article_ids: ArticleIdService | None = None,
        article_paths: ArticlePathService | None = None,
        get_article: Callable[[str], ArticleDetailDTO] | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.markdown = markdown or MarkdownService()
        self.blog_authors = blog_authors or BlogAuthorService()
        self.article_ids = article_ids or ArticleIdService()
        self.article_paths = article_paths or ArticlePathService()
        self.get_article = get_article

    def create_article_file(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        self.article_paths.validate_path_segment(payload.slug, field_name="slug")
        self.article_paths.validate_blog_category_path(payload.category_path)
        self.blog_authors.validate_authors(payload.authors)

        category_slug = payload.category_path[0]
        date_value = payload.date or self._now_shanghai_iso()
        last_update = payload.last_update if isinstance(payload.last_update, dict) else {}
        last_update_date = self._string_value(last_update.get("date")) or date_value
        last_update_author = self._string_value(last_update.get("author")) or BlogAuthorService.first_author(payload.authors)
        relative_path = "/".join([category_slug, f"{payload.slug}.md"])
        path = self.filesystem.resolve_article_path(ArticleType.blog, relative_path)
        if path.exists():
            raise ConflictError("blog 文章已存在。", code="article_already_exists")

        frontmatter: dict[str, Any] = {
            "slug": payload.slug,
            "title": payload.title,
            "authors": payload.authors[0] if len(payload.authors) == 1 else payload.authors,
            "date": date_value,
            "last_update": {
                "date": last_update_date,
                "author": last_update_author,
            },
            "description": payload.description or "",
            "tags": payload.tags,
        }

        raw_content = self.markdown.compose(frontmatter, payload.body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw_content, encoding="utf-8")

        return self._get_created_article(ArticleType.blog, relative_path)

    def _get_created_article(self, article_type: ArticleType, relative_path: str) -> ArticleDetailDTO:
        if self.get_article is None:
            raise RuntimeError("BlogArticleService requires get_article to return created article details.")
        return self.get_article(self.article_ids.encode(article_type, relative_path))

    @staticmethod
    def _now_shanghai_iso() -> str:
        return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
