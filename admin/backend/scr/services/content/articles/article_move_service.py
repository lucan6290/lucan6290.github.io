"""Article move and rename operations."""

from __future__ import annotations

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleMoveDTO
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.articles.article_category_index_sync_service import ArticleCategoryIndexSyncService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_move_image_service import ArticleMoveImageService
from scr.services.content.articles.article_move_target_service import ArticleMoveTargetService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.articles.article_reference_service import ArticleReferenceService
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleMoveService:
    """Move articles, update nearby metadata, and optionally replace old links."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        markdown: MarkdownService | None = None,
        sidebar: SidebarService | None = None,
        category: CategoryService | None = None,
        category_index: CategoryIndexService | None = None,
        article_ids: ArticleIdService | None = None,
        article_paths: ArticlePathService | None = None,
        article_references: ArticleReferenceService | None = None,
        article_move_images: ArticleMoveImageService | None = None,
        article_move_targets: ArticleMoveTargetService | None = None,
        category_index_sync: ArticleCategoryIndexSyncService | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.markdown = markdown or MarkdownService()
        self.sidebar = sidebar or SidebarService()
        self.category = category or CategoryService()
        self.category_index = category_index or CategoryIndexService()
        self.article_ids = article_ids or ArticleIdService()
        self.article_paths = article_paths or ArticlePathService()
        self.article_references = article_references or ArticleReferenceService(
            filesystem=self.filesystem,
            sidebar=self.sidebar,
        )
        self.article_move_images = article_move_images or ArticleMoveImageService()
        self.article_move_targets = article_move_targets or ArticleMoveTargetService(
            article_paths=self.article_paths,
            category=self.category,
        )
        self.category_index_sync = category_index_sync or ArticleCategoryIndexSyncService(
            category=self.category,
            category_index=self.category_index,
        )
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()

    def move_article(self, article_id: str, payload: ArticleMoveDTO) -> MutationPlanDTO:
        """移动或重命名文章；默认只返回影响分析。"""
        article_type, relative_path = self.article_ids.decode(article_id)
        if payload.target_type != article_type:
            raise BadRequestError(
                "当前仅支持在同一内容类型内移动或重命名文章。",
                code="invalid_target_type",
                details={"source_type": article_type.value, "target_type": payload.target_type.value},
            )

        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        self.article_paths.validate_path_segment(payload.target_slug, field_name="target_slug")
        raw_content = article_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        target_relative_path, new_frontmatter = self.article_move_targets.build_target(
            article_type,
            relative_path,
            payload,
            parsed,
        )
        if payload.target_type == ArticleType.docs:
            self.article_move_targets.ensure_existing_docs_category_path(payload.target_category_path)
        target_path = self.filesystem.resolve_article_path(payload.target_type, target_relative_path)
        if target_path.exists():
            raise ConflictError("目标文章已存在。", code="target_article_exists")

        image_dir = self.article_move_images.image_dir_for(article_path)
        target_image_dir = self.article_move_images.image_dir_for(target_path)
        has_image_dir = image_dir.exists() and image_dir.is_dir()
        updated_body = (
            self.article_move_images.replace_dir_refs(parsed.body, image_dir.name, target_image_dir.name)
            if has_image_dir
            else parsed.body
        )
        if has_image_dir and target_image_dir.exists():
            raise ConflictError(
                "目标文章图片目录已存在。",
                code="target_article_exists",
                details={"target": self.filesystem.project_relative_posix_path(target_image_dir)},
            )

        old_doc_id = self.sidebar.doc_id_from_relative_path(relative_path) if article_type == ArticleType.docs else None
        new_doc_id = (
            self.sidebar.doc_id_from_relative_path(target_relative_path)
            if payload.target_type == ArticleType.docs
            else None
        )
        if old_doc_id and not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")
        sidebar_registered = old_doc_id in self.sidebar.list_registered_doc_ids() if old_doc_id else False
        target_category_labels = (
            self.category_index_sync.category_labels_for_path(payload.target_category_path)
            if payload.target_type == ArticleType.docs
            else []
        )
        moving_between_categories = (
            article_type == ArticleType.docs
            and payload.target_type == ArticleType.docs
            and self.article_paths.category_path(ArticleType.docs, relative_path, parsed.frontmatter) != payload.target_category_path
        )
        blog_target_category_path: list[str] = []
        blog_target_category_label: str | None = None
        moving_blog_between_categories = False
        if article_type == ArticleType.blog:
            blog_target_category_path = self.article_paths.category_path(
                ArticleType.blog,
                target_relative_path,
                new_frontmatter,
            )
            current_blog_category_path = self.article_paths.category_path(
                ArticleType.blog,
                relative_path,
                parsed.frontmatter,
            )
            moving_blog_between_categories = current_blog_category_path != blog_target_category_path
            if blog_target_category_path:
                _, blog_target_category_label = self.category.resolve_article_category(
                    ArticleType.blog,
                    blog_target_category_path,
                )
        link_replacements = self.article_references.moved_article_link_replacements(
            article_type,
            relative_path,
            target_relative_path,
            parsed.frontmatter,
            new_frontmatter,
        )
        link_changes = (
            self.article_references.find_replacement_target_paths(link_replacements, exclude_path=article_path)
            if payload.replace_links
            else []
        )

        if not payload.dry_run and not payload.confirm:
            raise BadRequestError("移动文章需要显式确认。", code="confirmation_required")

        warnings: list[str] = []
        if not payload.replace_links and self.article_references.find_replacement_target_paths(link_replacements, exclude_path=article_path):
            warnings.append("站内旧链接不会自动替换，除非 replace_links=true。")
        if old_doc_id and not sidebar_registered:
            warnings.append("原 docs 文章 ID 未登记在 sidebars.ts，移动时不会产生侧边栏替换。")

        changes = [
            FileChangeDTO(
                action="move",
                target=self.filesystem.project_relative_posix_path(target_path),
                from_=self.filesystem.project_relative_posix_path(article_path),
                to=self.filesystem.project_relative_posix_path(target_path),
                description="移动文章文件" if payload.dry_run else "已移动文章文件",
            )
        ]

        if has_image_dir:
            changes.append(
                FileChangeDTO(
                    action="move",
                    target=self.filesystem.project_relative_posix_path(target_image_dir),
                    from_=self.filesystem.project_relative_posix_path(image_dir),
                    to=self.filesystem.project_relative_posix_path(target_image_dir),
                    description="移动文章图片目录" if payload.dry_run else "已移动文章图片目录",
                )
            )

        if updated_body != parsed.body:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.filesystem.project_relative_posix_path(target_path),
                    description="更新文章内图片目录引用" if payload.dry_run else "已更新文章内图片目录引用",
                )
            )

        if old_doc_id and new_doc_id and sidebar_registered and old_doc_id != new_doc_id:
            changes.append(
                FileChangeDTO(
                    action="move" if moving_between_categories else "replace",
                    target=self.filesystem.project_relative_posix_path(settings.sidebars_path),
                    from_=old_doc_id,
                    to=new_doc_id,
                    description=(
                        "移动 docs 文章侧边栏位置"
                        if moving_between_categories and payload.dry_run
                        else "已移动 docs 文章侧边栏位置"
                        if moving_between_categories
                        else "替换 docs 文章 ID"
                        if payload.dry_run
                        else "已替换 docs 文章 ID"
                    ),
                )
            )

        for path in link_changes:
            changes.append(
                FileChangeDTO(
                    action="replace",
                    target=self.filesystem.project_relative_posix_path(path),
                    description="替换站内旧链接" if payload.dry_run else "已替换站内旧链接",
                )
            )

        if article_type == ArticleType.docs:
            for change in self.category_index_sync.preview_changes([relative_path, target_relative_path]):
                changes.append(change)
        if article_type == ArticleType.blog:
            if moving_blog_between_categories and blog_target_category_path:
                changes.append(
                    FileChangeDTO(
                        action="update",
                        target=self.filesystem.project_relative_posix_path(settings.docusaurus_config_path),
                        description="同步博客顶部导航一级分类" if payload.dry_run else "已同步博客顶部导航一级分类",
                    )
                )
            changes.extend(
                [
                    FileChangeDTO(
                        action="update",
                        target=self.filesystem.project_relative_posix_path(settings.blog_sidebars_path),
                        description="同步 blog 侧边栏" if payload.dry_run else "已同步 blog 侧边栏",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.filesystem.project_relative_posix_path(settings.blog_dir / "index.md"),
                        description="同步 blog 总目录页" if payload.dry_run else "已同步 blog 总目录页",
                    ),
                ]
            )

        plan = MutationPlanDTO(
            dry_run=payload.dry_run,
            requires_confirmation=payload.dry_run,
            changes=changes,
            warnings=warnings,
        )

        if payload.dry_run:
            return plan

        if article_type == ArticleType.blog:
            labels = self.category.ensure_category_path(
                ArticleType.blog,
                self.article_paths.category_path(ArticleType.blog, target_relative_path, new_frontmatter),
            )
            if labels:
                blog_target_category_label = labels[0]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if article_type == ArticleType.blog or updated_body != parsed.body:
            article_path.write_text(self.markdown.compose(new_frontmatter, updated_body), encoding="utf-8")

        if old_doc_id and new_doc_id and sidebar_registered and old_doc_id != new_doc_id:
            if moving_between_categories:
                self.sidebar.move_doc_id_to_existing_category(old_doc_id, new_doc_id, target_category_labels)
            else:
                self.sidebar.replace_doc_id(old_doc_id, new_doc_id)

        if payload.replace_links:
            self.article_references.replace_article_links(link_replacements, exclude_path=article_path)

        article_path.replace(target_path)
        if has_image_dir:
            self.article_move_images.move_dir(image_dir, target_image_dir)

        if article_type == ArticleType.docs:
            self.category_index.remove_doc_link(relative_path)
            self.category_index_sync.upsert_doc_link(target_relative_path, new_frontmatter)
            self.docs_sync.sync_after_article_change(
                [relative_path, target_relative_path],
                sync_type="docs_article_move",
            )
        if article_type == ArticleType.blog:
            self.blog_sync.sync_after_article_change(
                blog_target_category_path[0] if blog_target_category_path else None,
                blog_target_category_label,
            )

        return plan
