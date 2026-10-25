"""文章列表查询服务。"""

from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleListResponseDTO, ArticleSummaryDTO
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleQueryService:
    """负责文章列表扫描、过滤、排序与分页。"""

    sortable_fields = {"title", "date", "updated_at", "relative_path", "type"}

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        sidebar: SidebarService,
        summary: ArticleSummaryService,
        blog_authors: BlogAuthorService,
    ) -> None:
        self.filesystem = filesystem
        self.sidebar = sidebar
        self.summary = summary
        self.blog_authors = blog_authors

    def list_articles(
        self,
        article_type: ArticleType | None = None,
        keyword: str | None = None,
        tag: str | None = None,
        author: str | None = None,
        category: str | None = None,
        has_issues: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str | None = None,
    ) -> ArticleListResponseDTO:
        """列出文章摘要，支持过滤、排序与分页。"""
        requested_types = [article_type] if article_type else [ArticleType.docs, ArticleType.blog]
        registered_doc_ids = self.sidebar.list_registered_doc_ids()
        known_blog_authors = self.blog_authors.load_authors()

        articles: list[ArticleSummaryDTO] = []
        for current_type in requested_types:
            for path in self.filesystem.scan_article_files(current_type):
                summary = self.summary.build_summary(path, current_type, registered_doc_ids, known_blog_authors)
                if self.matches_filters(
                    summary,
                    keyword=keyword,
                    tag=tag,
                    author=author,
                    category=category,
                    has_issues=has_issues,
                ):
                    articles.append(summary)

        articles = self.sort_articles(articles, sort)
        total = len(articles)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        return ArticleListResponseDTO(
            items=articles[start_index:end_index],
            page=page,
            page_size=page_size,
            total=total,
            has_next=end_index < total,
        )

    def matches_filters(
        self,
        summary: ArticleSummaryDTO,
        *,
        keyword: str | None,
        tag: str | None,
        author: str | None,
        category: str | None,
        has_issues: bool | None,
    ) -> bool:
        """聚合列表接口的过滤条件。"""
        if not self.matches_keyword(summary, keyword):
            return False
        if tag and tag not in summary.tags:
            return False
        if author and author not in summary.authors:
            return False
        if category:
            normalized_category = category.strip("/")
            current_category = "/".join(summary.category_path)
            if not current_category.startswith(normalized_category):
                return False
        return not (has_issues is True and not summary.issues)

    @staticmethod
    def matches_keyword(summary: ArticleSummaryDTO, keyword: str | None) -> bool:
        """关键词命中检测：在标题、描述、路径、slug、标签中做大小写不敏感包含匹配。"""
        if not keyword:
            return True

        normalized = keyword.lower()
        fields = [
            summary.title or "",
            summary.description or "",
            summary.relative_path,
            summary.slug,
            " ".join(summary.tags),
        ]
        return any(normalized in field.lower() for field in fields)

    def sort_articles(self, articles: list[ArticleSummaryDTO], sort: str | None) -> list[ArticleSummaryDTO]:
        """按文档约定字段排序；字段前缀 '-' 表示倒序，便于前端使用。"""
        if not sort:
            return articles

        descending = sort.startswith("-")
        field_name = sort[1:] if descending else sort
        if field_name not in self.sortable_fields:
            raise BadRequestError("sort 字段不支持。", code="invalid_sort_field", details={"sort": sort})

        return sorted(
            articles,
            key=lambda article: self.article_sort_value(article, field_name),
            reverse=descending,
        )

    @staticmethod
    def article_sort_value(article: ArticleSummaryDTO, field_name: str) -> str:
        """返回列表排序值。"""
        if field_name == "title":
            return article.title or ""
        if field_name == "date":
            return article.date or ""
        if field_name == "updated_at":
            return article.updated_at
        if field_name == "relative_path":
            return article.relative_path
        if field_name == "type":
            return article.type.value
        return ""
