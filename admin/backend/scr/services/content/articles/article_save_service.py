"""Article save use cases."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError, PreconditionRequiredError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleDetailDTO, ArticleUpdateDTO, ValidationIssueDTO
from scr.services.content.articles.article_category_index_sync_service import ArticleCategoryIndexSyncService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


class ArticleSaveService:
    """Save article front matter and body without changing the file path."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        article_ids: ArticleIdService,
        article_paths: ArticlePathService,
        article_summaries: ArticleSummaryService,
        category_index_sync: ArticleCategoryIndexSyncService,
        blog_authors: BlogAuthorService,
        get_article: Callable[[str], ArticleDetailDTO] | None,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.article_ids = article_ids
        self.article_paths = article_paths
        self.article_summaries = article_summaries
        self.category_index_sync = category_index_sync
        self.blog_authors = blog_authors
        self._get_article = get_article
        self.docs_sync = DocsContentSyncService()

    def save_article(self, article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
        if not payload.expected_version or not payload.expected_version.strip():
            raise PreconditionRequiredError("缺少 expected_version。", code="version_required")

        article_type, relative_path = self.article_ids.decode(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        current_version = ArticleSummaryService.file_version(path)
        if payload.expected_version != current_version:
            raise ConflictError(
                "文件版本已变化，请重新读取后再保存。",
                code="version_conflict",
                details={
                    "expected_version": payload.expected_version,
                    "current_version": current_version,
                },
            )

        self.validate_update_frontmatter(article_type, payload.frontmatter)
        if article_type == ArticleType.docs:
            existing_last_update = payload.frontmatter.get("last_update")
            existing_author = (
                existing_last_update.get("author")
                if isinstance(existing_last_update, dict)
                else None
            ) or "lucan"
            payload.frontmatter["last_update"] = {
                "date": self.now_shanghai_iso(),
                "author": existing_author,
            }
        else:
            payload.frontmatter["last_update"] = {
                "date": self.now_shanghai_iso(),
                "author": self.blog_authors.last_update_author(payload.frontmatter),
            }

        raw_content = self.markdown.compose(payload.frontmatter, payload.body)
        path.write_text(raw_content, encoding="utf-8")
        if article_type == ArticleType.docs:
            self.category_index_sync.upsert_doc_link(relative_path, payload.frontmatter)
            self.docs_sync.sync_after_article_change(
                [relative_path],
                sync_type="docs_article_save",
            )

        if self._get_article is None:
            raise RuntimeError("Article detail reader is not configured.")
        return self._get_article(article_id)

    def validate_update_frontmatter(self, article_type: ArticleType, frontmatter: dict[str, Any]) -> None:
        issues: list[ValidationIssueDTO]
        if article_type == ArticleType.docs:
            issues = self.article_summaries.validate_docs(frontmatter, sidebar_registered=True)
            blocking_issues = [
                issue
                for issue in issues
                if issue.severity == "error" and issue.code != "docs_sidebar_missing"
            ]
        else:
            issues = self.article_summaries.validate_blog(frontmatter, self.blog_authors.load_authors())
            blocking_issues = [issue for issue in issues if issue.severity == "error"]

            slug = self.article_paths.string_value(frontmatter.get("slug"))
            if slug and not self.article_paths.is_safe_path_segment(slug):
                raise BadRequestError(
                    "Front Matter 不符合内容类型规则。",
                    code="frontmatter_invalid",
                    details={"issues": [{"code": "invalid_path_segment", "message": "blog slug 不能包含路径危险字符。"}]},
                )

        if blocking_issues:
            raise BadRequestError(
                "Front Matter 不符合内容类型规则。",
                code="frontmatter_invalid",
                details={"issues": [issue.model_dump() for issue in blocking_issues]},
            )

    @staticmethod
    def now_shanghai_iso() -> str:
        return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
