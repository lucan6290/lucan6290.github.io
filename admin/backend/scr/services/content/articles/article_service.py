"""文章业务服务层（content 子包）。

协调 FileSystemService、MarkdownService 与 SidebarService，提供文章的
列表查询、详情读取、创建写入，以及 Front Matter 校验与文章 ID 编解码。
docs 与 blog 两种类型在路径约定、frontmatter 字段与侧边栏登记上存在差异，
由各自的私有方法分别处理。
"""

from pathlib import Path

from scr.models.article import ArticleType
from scr.schemas.article import (
    ArticleDetailDTO,
    ArticleImageCheckDTO,
    ArticleImageListDTO,
    ArticleListResponseDTO,
    ArticleMoveDTO,
    ArticleUpdateDTO,
    ArticleValidationResultDTO,
    ImageDTO,
)
from scr.schemas.common import MutationPlanDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_detail_service import ArticleDetailService
from scr.services.content.articles.article_image_management_service import ArticleImageManagementService
from scr.services.content.articles.article_image_service import ArticleImageService
from scr.services.content.articles.article_image_reference_service import ArticleImageReferenceService
from scr.services.content.articles.article_move_service import ArticleMoveService
from scr.services.content.articles.article_mutation_service import ArticleMutationService
from scr.services.content.articles.article_query_service import ArticleQueryService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.articles.article_validation_service import ArticleValidationService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleService:
    """文章核心业务服务，供 API 端点直接调用。"""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.sidebar = SidebarService()
        self.category = CategoryService()
        self.category_index = CategoryIndexService()
        self.article_ids = ArticleIdService()
        self.images = ArticleImageService()
        self.image_references = ArticleImageReferenceService()
        self.blog_authors = BlogAuthorService()
        self.article_image_management = ArticleImageManagementService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            article_ids=self.article_ids,
            images=self.images,
            image_references=self.image_references,
        )
        self.article_summaries = ArticleSummaryService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category=self.category,
            article_ids=self.article_ids,
        )
        self.article_details = ArticleDetailService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            summary=self.article_summaries,
            blog_authors=self.blog_authors,
            article_ids=self.article_ids,
        )
        self.article_validation = ArticleValidationService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            summary=self.article_summaries,
            blog_authors=self.blog_authors,
            article_ids=self.article_ids,
            image_references=self.image_references,
        )
        self.article_queries = ArticleQueryService(
            filesystem=self.filesystem,
            sidebar=self.sidebar,
            summary=self.article_summaries,
            blog_authors=self.blog_authors,
        )
        self.article_moves = ArticleMoveService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category=self.category,
            category_index=self.category_index,
            article_ids=self.article_ids,
        )
        self.article_mutations = ArticleMutationService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category=self.category,
            category_index=self.category_index,
            article_ids=self.article_ids,
            article_summaries=self.article_summaries,
            blog_authors=self.blog_authors,
            get_article=self.get_article,
        )

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
        """列出文章摘要，支持过滤、排序与分页。

        article_type 为 None 时同时扫描 docs 与 blog；keyword 命中标题/描述/路径/标签等任一字段即保留。
        """
        return self.article_queries.list_articles(
            article_type=article_type,
            keyword=keyword,
            tag=tag,
            author=author,
            category=category,
            has_issues=has_issues,
            page=page,
            page_size=page_size,
            sort=sort,
        )

    def get_article(self, article_id: str) -> ArticleDetailDTO:
        """根据文章 ID 读取详情；文件不存在时抛 NotFoundError。"""
        return self.article_details.get_article(article_id)

    def save_article(self, article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
        """保存文章内容，不改变文章路径，并使用 expected_version 做乐观锁校验。"""
        return self.article_mutations.save_article(article_id, payload)

    def validate_article(self, article_id: str) -> ArticleValidationResultDTO:
        """校验单篇文章，返回 Front Matter、侧边栏与本地图片引用问题。"""
        return self.article_validation.validate_article(article_id)

    def encode_article_id(self, article_type: ArticleType, relative_path: str) -> str:
        """将文章类型与相对路径编码为对外 article_id。"""
        return self.article_ids.encode(article_type, relative_path)

    def list_article_images(self, article_id: str) -> ArticleImageListDTO:
        """列出文章同名图片目录中的图片资源。"""
        return self.article_image_management.list_article_images(article_id)

    def upload_article_image(
        self,
        article_id: str,
        *,
        original_filename: str,
        content_type: str | None,
        content: bytes,
        slug: str | None = None,
        alt: str | None = None,
    ) -> ImageDTO:
        """上传图片到文章同名图片目录，并返回可插入 Markdown 的图片信息。"""
        return self.article_image_management.upload_article_image(
            article_id,
            original_filename=original_filename,
            content_type=content_type,
            content=content,
            slug=slug,
            alt=alt,
        )

    def check_article_images(self, article_id: str) -> ArticleImageCheckDTO:
        """检查文章图片目录与正文图片引用之间的差异。"""
        return self.article_image_management.check_article_images(article_id)

    def get_article_image_path(self, article_id: str, image_name: str) -> Path:
        """返回文章同名图片目录中的安全图片路径。"""
        return self.article_image_management.get_article_image_path(article_id, image_name)

    def delete_article_image(
        self,
        article_id: str,
        image_name: str,
        *,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除文章同名图片目录中的单个图片，默认只返回影响分析。"""
        return self.article_image_management.delete_article_image(
            article_id,
            image_name,
            dry_run=dry_run,
            confirm=confirm,
        )

    def delete_article(
        self,
        article_id: str,
        *,
        with_images: bool = False,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除文章文件；docs 文章会同步移除 sidebars.ts 中的 doc_id。"""
        return self.article_mutations.delete_article(
            article_id,
            with_images=with_images,
            dry_run=dry_run,
            confirm=confirm,
        )

    def move_article(self, article_id: str, payload: ArticleMoveDTO) -> MutationPlanDTO:
        """移动或重命名文章；默认只返回影响分析。"""
        return self.article_moves.move_article(article_id, payload)
