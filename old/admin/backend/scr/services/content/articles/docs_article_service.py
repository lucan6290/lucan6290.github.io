"""Docs article file operations."""

from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from scr.core.exceptions import ConflictError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


class DocsArticleService:
    """Create docs article files without orchestrating derived indexes."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        markdown: MarkdownService | None = None,
        category: CategoryService | None = None,
        article_ids: ArticleIdService | None = None,
        article_paths: ArticlePathService | None = None,
        get_article: Callable[[str], ArticleDetailDTO] | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.markdown = markdown or MarkdownService()
        self.category = category or CategoryService()
        self.article_ids = article_ids or ArticleIdService()
        self.article_paths = article_paths or ArticlePathService()
        self.get_article = get_article

    def create_article_file(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        self.article_paths.validate_path_segment(payload.slug, field_name="slug")
        for segment in payload.category_path:
            self.article_paths.validate_path_segment(segment, field_name="category_path")

        relative_path = "/".join([*payload.category_path, f"{payload.slug}.md"])
        path = self.filesystem.resolve_article_path(ArticleType.docs, relative_path)
        if path.exists():
            raise ConflictError("docs 文章已存在。", code="article_already_exists")

        self._ensure_existing_docs_category_path(payload.category_path)
        date_value = payload.date or self._now_shanghai_iso()
        authors_value = payload.authors[0] if len(payload.authors) == 1 else (payload.authors or ["lucan"])
        frontmatter: dict[str, object] = {
            "title": payload.title,
            "authors": authors_value,
            "date": date_value,
            "last_update": {
                "date": date_value,
                "author": "lucan",
            },
            "description": payload.description or "",
            "sidebar_position": payload.sidebar_position if payload.sidebar_position is not None else 1,
        }

        raw_content = self.markdown.compose(frontmatter, payload.body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw_content, encoding="utf-8")

        return self._get_created_article(ArticleType.docs, relative_path)

    def _get_created_article(self, article_type: ArticleType, relative_path: str) -> ArticleDetailDTO:
        if self.get_article is None:
            raise RuntimeError("DocsArticleService requires get_article to return created article details.")
        return self.get_article(self.article_ids.encode(article_type, relative_path))

    def _ensure_existing_docs_category_path(self, category_path: list[str]) -> None:
        if not category_path:
            return
        if not self.category.category_path_exists(ArticleType.docs, category_path):
            raise NotFoundError(
                "docs 分类不存在，请先通过分类接口创建分类。",
                code="category_not_found",
                details={"category_path": category_path},
            )

    @staticmethod
    def _now_shanghai_iso() -> str:
        return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
