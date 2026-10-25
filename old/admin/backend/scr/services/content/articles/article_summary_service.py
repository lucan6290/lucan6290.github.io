"""文章摘要构建服务。"""

from datetime import datetime
import re
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scr.models.article import ArticleType
from scr.schemas.article import ArticleSummaryDTO, ValidationIssueDTO
from scr.services.content.articles.article_frontmatter_validation_service import ArticleFrontmatterValidationService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService, ParsedMarkdown
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleSummaryService:
    """负责由 markdown 文件构建文章摘要及摘要相关辅助值。"""

    date_slug_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        sidebar: SidebarService,
        category: CategoryService,
        article_ids: ArticleIdService,
        frontmatter_validation: ArticleFrontmatterValidationService | None = None,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.sidebar = sidebar
        self.category = category
        self.article_ids = article_ids
        self.frontmatter_validation = frontmatter_validation or ArticleFrontmatterValidationService()

    def build_summary(
        self,
        path: Path,
        article_type: ArticleType,
        registered_doc_ids: set[str],
        blog_authors: set[str],
        parsed: ParsedMarkdown | None = None,
    ) -> ArticleSummaryDTO:
        """由文件路径与解析结果组装文章摘要，并附加类型相关的校验问题。"""
        raw_content = path.read_text(encoding="utf-8")
        parsed = parsed or self.markdown.parse(raw_content)
        relative_path = self.filesystem.relative_posix_path(article_type, path)
        frontmatter = parsed.frontmatter

        slug = self.resolve_slug(article_type, relative_path, frontmatter)
        issues = [*parsed.issues]
        sidebar_registered: bool | None = None

        if article_type == ArticleType.docs:
            doc_id = self.sidebar.doc_id_from_relative_path(relative_path)
            slug = doc_id
            sidebar_registered = doc_id in registered_doc_ids
            issues.extend(self.validate_docs(frontmatter, sidebar_registered))
        else:
            issues.extend(self.validate_blog(frontmatter, blog_authors))

        tags = self.list_value(frontmatter.get("tags"))
        category_path, category_label = self.category.resolve_article_category(
            article_type,
            self.category_path(article_type, relative_path, frontmatter),
            self.category_candidates(frontmatter),
        )

        return ArticleSummaryDTO(
            id=self.article_ids.encode(article_type, relative_path),
            type=article_type,
            type_label=self.category.type_label(article_type),
            title=self.string_value(frontmatter.get("title")),
            description=self.string_value(frontmatter.get("description")),
            date=self.string_value(frontmatter.get("date")),
            last_update=frontmatter.get("last_update") if isinstance(frontmatter.get("last_update"), dict) else None,
            relative_path=relative_path,
            route=self.build_route(article_type, slug),
            slug=slug,
            tags=tags,
            authors=self.list_value(frontmatter.get("authors")),
            category_path=category_path,
            category_label=category_label,
            sidebar_registered=sidebar_registered,
            version=self.file_version(path),
            updated_at=self.file_updated_at(path),
            issues=issues,
        )

    def validate_docs(self, frontmatter: dict[str, Any], sidebar_registered: bool) -> list[ValidationIssueDTO]:
        """校验 docs 文章：title 必填、description 建议、必须登记到 sidebars.ts。"""
        return self.frontmatter_validation.validate_docs(frontmatter, sidebar_registered)

    def validate_blog(self, frontmatter: dict[str, Any], known_authors: set[str]) -> list[ValidationIssueDTO]:
        """校验 blog 文章：title/slug/authors/date/last_update 必填，tags 可为空。"""
        return self.frontmatter_validation.validate_blog(frontmatter, known_authors)

    def resolve_slug(
        self,
        article_type: ArticleType,
        relative_path: str,
        frontmatter: dict[str, Any],
    ) -> str:
        """解析文章 slug：docs 固定取 doc_id；blog 依次取 frontmatter.slug、文件名。"""
        if article_type == ArticleType.docs:
            return self.sidebar.doc_id_from_relative_path(relative_path)

        frontmatter_slug = self.string_value(frontmatter.get("slug"))
        if frontmatter_slug:
            return frontmatter_slug

        stem = Path(relative_path).stem
        match = self.date_slug_pattern.match(stem)
        return match.group("slug") if match else stem

    @staticmethod
    def build_route(article_type: ArticleType, slug: str) -> str:
        """根据类型与 slug 拼接前端访问路由。"""
        if article_type == ArticleType.docs:
            return f"/docs/{slug}"
        return f"/blog/{slug}"

    @staticmethod
    def category_path(article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> list[str]:
        """提取文章分类路径；docs 与 blog 均来自文件所在目录。"""
        parts = Path(relative_path).parent.as_posix().split("/")
        if parts == ["."]:
            return []
        if article_type == ArticleType.blog:
            return parts[:1]
        return parts

    def category_candidates(self, frontmatter: dict[str, Any]) -> list[str]:
        """从 frontmatter 中提取可用于分类显示名匹配的候选值。"""
        candidates: list[str] = []
        candidates.extend(self.list_value(frontmatter.get("category")))
        candidates.extend(self.list_value(frontmatter.get("categories")))
        candidates.extend(self.list_value(frontmatter.get("tags")))
        return candidates

    @staticmethod
    def file_version(path: Path) -> str:
        """基于文件修改时间与大小生成乐观锁版本。"""
        stat = path.stat()
        return f"mtime:{stat.st_mtime_ns}:size:{stat.st_size}"

    @staticmethod
    def file_updated_at(path: Path) -> str:
        """返回文件最后修改时间的上海时区 ISO 字符串。"""
        return datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    @staticmethod
    def string_value(value: Any) -> str | None:
        """将任意值规范化为字符串，None 透传。"""
        if value is None:
            return None
        return str(value)

    @staticmethod
    def list_value(value: Any) -> list[str]:
        """将标量或列表统一规整为字符串列表。"""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @classmethod
    def is_safe_path_segment(cls, value: str) -> bool:
        """校验单个路径片段是否可安全用于本地文件名。"""
        return ArticleFrontmatterValidationService.is_safe_path_segment(value)
