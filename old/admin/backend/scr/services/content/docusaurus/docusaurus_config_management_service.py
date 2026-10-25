"""Docusaurus 站点配置对账与同步服务。

对账 ``docusaurus.config.ts`` 的 ``navbar.items`` 与 docs/blog 实际内容：
- 断链检查：navbar 内部链接（``to:``）指向的 docs/blog 路径是否存在；
- 缺失检查：docs 一级分类是否已登记到知识库 dropdown。

同步提供两种动作：追加缺失的 docs 一级分类入口、清理断链导航项。
两种动作均采用 dry_run + confirm 二段式确认，与 sidebars 对账层对齐。
"""

from __future__ import annotations

from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.schemas.docusaurus_config import (
    BlogTopCategoryNavDTO,
    DocusaurusConfigNavItemDTO,
    DocusaurusConfigStatusDTO,
    DocsTopCategoryNavDTO,
)
from scr.services.content.categories.category_service import CategoryService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService


class DocusaurusConfigManagementService:
    """对账 navbar 与 docs/blog 内容，并执行安全同步。"""

    def __init__(self) -> None:
        self.config = DocusaurusConfigService()
        self.category = CategoryService()

    def get_status(self) -> DocusaurusConfigStatusDTO:
        """返回 navbar 内部链接与 docs 一级分类的对账状态。"""
        config_path = self._relative_path(settings.docusaurus_config_path)
        if not settings.docusaurus_config_path.exists():
            return DocusaurusConfigStatusDTO(
                config_exists=False,
                config_path=config_path,
                nav_item_total=0,
                nav_items=[],
                broken_to_links=[],
                docs_top_category_total=0,
                docs_top_categories_missing_in_nav=[],
            )

        blog_slugs = self.config.build_blog_slug_index()
        blog_category_slugs = self.config.build_blog_category_index()
        raw_items = self.config.list_navbar_to_items()
        nav_items = [
            DocusaurusConfigNavItemDTO(
                to=item.to,
                label=item.label,
                dropdown_label=item.dropdown_label,
                exists=self.config.check_to_link_exists(
                    item.to,
                    blog_slugs=blog_slugs,
                    blog_category_slugs=blog_category_slugs,
                ),
            )
            for item in raw_items
        ]
        broken = [item for item in nav_items if item.exists is False]

        top_categories = self._docs_top_categories()
        registered_top_slugs = self._registered_docs_top_slugs(raw_items)
        missing_docs = [
            DocsTopCategoryNavDTO(slug=slug, label=label)
            for slug, label in top_categories
            if slug not in registered_top_slugs
        ]
        blog_top_categories = self._blog_top_categories()
        registered_blog_top_slugs = self._registered_blog_top_slugs(raw_items)
        blog_top_slugs = {slug for slug, _ in blog_top_categories}
        missing_blog = [
            BlogTopCategoryNavDTO(slug=slug, label=label)
            for slug, label in blog_top_categories
            if slug not in registered_blog_top_slugs
        ]
        stale_blog_nav_items = self._stale_blog_nav_items(nav_items, blog_top_slugs)

        return DocusaurusConfigStatusDTO(
            config_exists=True,
            config_path=config_path,
            nav_item_total=len(nav_items),
            nav_items=nav_items,
            broken_to_links=broken,
            docs_top_category_total=len(top_categories),
            docs_top_categories_missing_in_nav=missing_docs,
            blog_top_category_total=len(blog_top_categories),
            blog_top_categories_missing_in_nav=missing_blog,
            stale_blog_nav_items=stale_blog_nav_items,
        )

    def sync(self, payload) -> MutationPlanDTO:
        """同步 navbar：追加缺失的 docs 一级分类入口、清理断链。"""
        if not settings.docusaurus_config_path.exists():
            raise NotFoundError("site/docusaurus.config.ts 不存在。", code="docusaurus_config_missing")
        if payload.mode not in {"append_missing_top", "remove_broken", "all"}:
            raise BadRequestError(
                "不支持的同步模式。",
                code="unsupported_docusaurus_config_sync_mode",
                details={"mode": payload.mode},
            )
        if not payload.dry_run and not payload.confirm:
            raise BadRequestError("同步 docusaurus 配置需要显式确认。", code="confirmation_required")

        status = self.get_status()
        do_append = payload.mode in {"append_missing_top", "all"}
        do_remove = payload.mode in {"remove_broken", "all"}

        target = self._relative_path(settings.docusaurus_config_path)
        changes: list[FileChangeDTO] = []
        warnings: list[str] = []

        if do_append:
            for missing_cat in status.docs_top_categories_missing_in_nav:
                changes.append(
                    FileChangeDTO(
                        action="update",
                        target=target,
                        description=(
                            f"追加 docs 一级分类「{missing_cat.label}」到知识库导航（to: /docs/{missing_cat.slug}）"
                            if payload.dry_run
                            else f"已追加 docs 一级分类「{missing_cat.label}」到知识库导航"
                        ),
                    )
                )
            for missing_cat in status.blog_top_categories_missing_in_nav:
                changes.append(
                    FileChangeDTO(
                        action="update",
                        target=target,
                        description=(
                            f"追加 blog 一级分类「{missing_cat.label}」到博客导航（to: /blog/{missing_cat.slug}）"
                            if payload.dry_run
                            else f"已追加 blog 一级分类「{missing_cat.label}」到博客导航"
                        ),
                    )
                )
        if do_remove:
            broken_tos = {item.to for item in status.broken_to_links}
            for broken_item in status.broken_to_links:
                dropdown_hint = f"，所属 dropdown：{broken_item.dropdown_label}" if broken_item.dropdown_label else ""
                changes.append(
                    FileChangeDTO(
                        action="delete",
                        target=target,
                        description=(
                            f"移除断链导航项 to: {broken_item.to}（label: {broken_item.label or '无'}{dropdown_hint}）"
                            if payload.dry_run
                            else f"已移除断链导航项 to: {broken_item.to}"
                        ),
                    )
                )
            for stale_item in status.stale_blog_nav_items:
                if stale_item.to in broken_tos:
                    continue
                changes.append(
                    FileChangeDTO(
                        action="delete",
                        target=target,
                        description=(
                            f"移除博客导航中的非一级分类项 to: {stale_item.to}（label: {stale_item.label or '无'}）"
                            if payload.dry_run
                            else f"已移除博客导航中的非一级分类项 to: {stale_item.to}"
                        ),
                    )
                )

        if payload.dry_run:
            return MutationPlanDTO(dry_run=True, requires_confirmation=True, changes=changes, warnings=warnings)

        if do_append:
            for missing_cat in status.docs_top_categories_missing_in_nav:
                self.config.upsert_knowledge_nav_item(missing_cat.slug, missing_cat.label)
            for missing_cat in status.blog_top_categories_missing_in_nav:
                self.config.upsert_blog_nav_item(missing_cat.slug, missing_cat.label)
        if do_remove:
            for broken_item in status.broken_to_links:
                self.config.remove_nav_item_by_to(broken_item.to)
            for stale_item in status.stale_blog_nav_items:
                self.config.remove_nav_item_by_to(stale_item.to)

        return MutationPlanDTO(dry_run=False, requires_confirmation=False, changes=changes, warnings=warnings)

    def _docs_top_categories(self) -> list[tuple[str, str]]:
        """返回 docs 一级分类 ``(slug, label)``；要求存在可解析的路由目标。

        navbar 指向 ``/docs/{slug}``，必须命中 ``docs/{slug}.md`` 或
        ``docs/{slug}/index.md`` 才不会成为断链。注册表里登记但目录尚未建好的
        一级分类不纳入追加候选，避免追加后立即产生断链。
        """
        result: list[tuple[str, str]] = []
        for category in self.category.list_categories(
            article_type=ArticleType.docs,
            include_empty=True,
        ):
            if not category.path or len(category.path) != 1:
                continue
            slug = category.path[0]
            if self.config.check_to_link_exists(f"/docs/{slug}") is True:
                result.append((slug, category.label))
        return result

    def _blog_top_categories(self) -> list[tuple[str, str]]:
        """返回 blog 一级分类 ``(slug, label)``。"""
        result: list[tuple[str, str]] = []
        for category in self.category.list_categories(
            article_type=ArticleType.blog,
            include_empty=True,
        ):
            if not category.path or len(category.path) != 1:
                continue
            slug = category.path[0]
            if self.config.check_to_link_exists(f"/blog/{slug}") is True:
                result.append((slug, category.label))
        return result

    @staticmethod
    def _registered_docs_top_slugs(raw_items) -> set[str]:
        """从 navbar to-items 中提取已登记的 docs 一级 slug 集合。

        仅采纳单级路径（如 ``/docs/project-practice``）；``/docs/index`` 首页与
        多级路径（如 ``/docs/a/b``）不计入一级分类登记。
        """
        registered: set[str] = set()
        for item in raw_items:
            to = item.to
            if not to.startswith("/docs/") or to == "/docs/index":
                continue
            slug = to[len("/docs/"):].strip("/")
            if slug and "/" not in slug:
                registered.add(slug)
        return registered

    @staticmethod
    def _registered_blog_top_slugs(raw_items) -> set[str]:
        """从博客 dropdown 中提取已登记的 blog 一级 slug 集合。"""
        registered: set[str] = set()
        for item in raw_items:
            to = item.to
            if item.dropdown_label != "博客" or to == "/blog" or not to.startswith("/blog/"):
                continue
            slug = to[len("/blog/"):].strip("/")
            if slug and "/" not in slug:
                registered.add(slug)
        return registered

    @staticmethod
    def _stale_blog_nav_items(nav_items: list[DocusaurusConfigNavItemDTO], blog_top_slugs: set[str]) -> list[DocusaurusConfigNavItemDTO]:
        """返回博客 dropdown 中不再符合“首页 + 一级分类”规则的项目。"""
        stale: list[DocusaurusConfigNavItemDTO] = []
        for item in nav_items:
            if item.dropdown_label != "博客" or item.to == "/blog" or not item.to.startswith("/blog/"):
                continue
            slug = item.to[len("/blog/"):].strip("/")
            if not slug or "/" in slug:
                stale.append(item)
                continue
            if slug not in blog_top_slugs:
                stale.append(item)
        return stale

    @staticmethod
    def _relative_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
