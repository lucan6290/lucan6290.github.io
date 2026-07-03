"""Article move target calculation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleMoveDTO
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.markdown_service import ParsedMarkdown


class ArticleMoveTargetService:
    """Resolve target relative paths and front matter for article moves."""

    def __init__(
        self,
        *,
        article_paths: ArticlePathService,
        category: CategoryService,
    ) -> None:
        self.article_paths = article_paths
        self.category = category

    def build_target(
        self,
        article_type: ArticleType,
        relative_path: str,
        payload: ArticleMoveDTO,
        parsed: ParsedMarkdown,
    ) -> tuple[str, dict[str, Any]]:
        extension = Path(relative_path).suffix or ".md"
        frontmatter = dict(parsed.frontmatter)

        if article_type == ArticleType.docs:
            self.article_paths.validate_docs_category_path(payload.target_category_path)
            target_relative_path = "/".join([*payload.target_category_path, f"{payload.target_slug}{extension}"])
            return target_relative_path, frontmatter

        target_category_path = payload.target_category_path or self.article_paths.category_path(
            ArticleType.blog,
            relative_path,
            frontmatter,
        )
        self.article_paths.validate_blog_category_path(target_category_path)
        date_value = payload.target_date or self.article_paths.string_value(frontmatter.get("date"))
        if not date_value:
            raise BadRequestError(
                "blog 文章缺少 date，无法移动。",
                code="invalid_blog_date",
                details={"relative_path": relative_path},
            )
        frontmatter["slug"] = payload.target_slug
        frontmatter["date"] = date_value
        return "/".join([target_category_path[0], f"{payload.target_slug}{extension}"]), frontmatter

    def ensure_existing_docs_category_path(self, category_path: list[str]) -> None:
        """Article moves can only target existing docs categories."""
        if not category_path:
            return
        if not self.category.category_path_exists(ArticleType.docs, category_path):
            raise NotFoundError(
                "docs 分类不存在，请先通过分类接口创建分类。",
                code="category_not_found",
                details={"category_path": category_path},
            )
