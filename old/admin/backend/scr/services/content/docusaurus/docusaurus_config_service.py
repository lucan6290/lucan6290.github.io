"""Docusaurus 站点配置维护服务。

读取并维护 ``site/docusaurus.config.ts``，聚焦 ``themeConfig.navbar.items``：

- 维护知识库 dropdown 下 docs 一级分类入口的增删改（原 ``CategoryService`` 能力迁移至此）；
- 扫描全部 ``navbar.items`` 内部链接（``to:``），供对账层检查断链、按需清理。

TS 配置靠括号配对 + 字段正则解析，避免引入完整的 TS 解析器依赖。
"""

from __future__ import annotations

from pathlib import Path
import re

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType
from scr.services.content.docusaurus.docusaurus_config_parser_service import (
    DocusaurusConfigParserService,
    NavItemInfo,
)
from scr.services.content.docusaurus.docusaurus_nav_service import DocusaurusNavService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


class DocusaurusConfigService:
    """读取并维护 Docusaurus 顶部导航配置。"""

    _blog_date_prefix_re = re.compile(r"^\d{4}-\d{2}-\d{2}-")

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.parser = DocusaurusConfigParserService()
        self.nav = DocusaurusNavService()

    # ==================== 全量 navbar 扫描 ====================

    def list_navbar_to_items(self) -> list[NavItemInfo]:
        """扫描 ``navbar.items``，返回所有含 ``to:`` 的导航项（含 dropdown 子项）。"""
        if not settings.docusaurus_config_path.exists():
            return []
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        return self.parser.scan_navbar_to_items(content)

    # ==================== 断链校验 ====================

    def build_blog_slug_index(self) -> set[str]:
        """构建 blog slug 集合（frontmatter slug + 文件名推导），供断链校验复用。"""
        slugs: set[str] = set()
        for path in self.filesystem.scan_article_files(ArticleType.blog):
            frontmatter = self.markdown.parse(path.read_text(encoding="utf-8")).frontmatter
            fm_slug = str(frontmatter.get("slug") or "").strip()
            if fm_slug:
                slugs.add(fm_slug)
            file_slug = self._blog_slug_from_filename(path.name)
            if file_slug:
                slugs.add(file_slug)
        return slugs

    def build_blog_category_index(self) -> set[str]:
        """构建 blog 一级分类 slug 集合，供 ``/blog/{category}`` 校验复用。"""
        if not settings.blog_dir.exists():
            return set()
        return {
            path.name
            for path in settings.blog_dir.iterdir()
            if path.is_dir()
        }

    @staticmethod
    def resolve_to_link_kind(to: str) -> str | None:
        """对 navbar ``to:`` 链接分类：``'docs'`` / ``'blog'`` / ``None``（不校验）。

        ``/projects``、``/about`` 等自定义页面与外链返回 None，校验时跳过。
        """
        if not to or not to.startswith("/"):
            return None
        if to == "/docs" or to.startswith("/docs/"):
            return "docs"
        if to == "/blog" or to.startswith("/blog/"):
            return "blog"
        return None

    def check_to_link_exists(
        self,
        to: str,
        blog_slugs: set[str] | None = None,
        blog_category_slugs: set[str] | None = None,
    ) -> bool | None:
        """校验 ``to:`` 指向的内容是否存在；返回 ``None`` 表示不校验。"""
        kind = self.resolve_to_link_kind(to)
        if kind is None:
            return None
        if kind == "docs":
            return self._docs_to_exists(to)
        return self._blog_to_exists(
            to,
            blog_slugs or self.build_blog_slug_index(),
            blog_category_slugs or self.build_blog_category_index(),
        )

    def _docs_to_exists(self, to: str) -> bool:
        if to == "/docs":
            return settings.docs_dir.exists()
        rel = to[len("/docs/"):].strip("/")
        if not rel:
            return settings.docs_dir.exists()
        # 命中 docs/{rel}.md 或 docs/{rel}/index.md
        if (settings.docs_dir / f"{rel}.md").exists():
            return True
        return settings.docs_dir.joinpath(*rel.split("/"), "index.md").exists()

    def _blog_to_exists(self, to: str, blog_slugs: set[str], blog_category_slugs: set[str]) -> bool:
        if to == "/blog":
            return True  # 博客首页
        slug = to[len("/blog/"):].strip("/")
        if not slug:
            return True
        return slug in blog_slugs or slug in blog_category_slugs

    @classmethod
    def _blog_slug_from_filename(cls, filename: str) -> str:
        stem = Path(filename).stem
        return cls._blog_date_prefix_re.sub("", stem, count=1)

    # ==================== 按 to 删除任意 nav item（断链清理） ====================

    def remove_nav_item_by_to(self, to: str) -> bool:
        """按 ``to`` 值删除任意 navbar 项；写入变更返回 True，未命中返回 False。"""
        if not settings.docusaurus_config_path.exists():
            raise BadRequestError(
                "site/docusaurus.config.ts 不存在，无法清理导航。",
                code="docusaurus_config_missing",
            )
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.remove_nav_item_by_to(content, to)
        if updated is None:
            return False
        if updated == content:
            return False
        settings.docusaurus_config_path.write_text(updated, encoding="utf-8")
        return True

    # ==================== 知识库 dropdown 维护（迁移自 CategoryService） ====================

    def knowledge_nav_item_exists(self, slug: str) -> bool:
        if not settings.docusaurus_config_path.exists():
            return False
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        return self.nav.knowledge_nav_item_exists(content, slug)

    def upsert_knowledge_nav_item(self, slug: str, label: str) -> None:
        """在知识库 dropdown 中新增或更新一个 docs 一级分类入口。"""
        if not settings.docusaurus_config_path.exists():
            raise BadRequestError(
                "site/docusaurus.config.ts 不存在，无法同步知识库顶部导航。",
                code="docusaurus_config_missing",
            )
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.upsert_knowledge_nav_item(content, slug, label)
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def update_knowledge_nav_item_label(self, slug: str, label: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.update_knowledge_nav_item_label(content, slug, label)
        if updated and updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def replace_knowledge_nav_item(self, old_slug: str, new_slug: str, label: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.replace_knowledge_nav_item(content, old_slug, new_slug, label)
        if updated is None:
            updated = self.nav.insert_knowledge_nav_item(content, new_slug, label)
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def remove_knowledge_nav_item(self, slug: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.remove_knowledge_nav_item(content, slug)
        if updated is None:
            return
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def blog_nav_item_exists(self, slug: str) -> bool:
        if not settings.docusaurus_config_path.exists():
            return False
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        return self.nav.blog_nav_item_exists(content, slug)

    def upsert_blog_nav_item(self, slug: str, label: str) -> None:
        """在博客 dropdown 中新增或更新一个 blog 一级分类入口。"""
        if not settings.docusaurus_config_path.exists():
            raise BadRequestError(
                "site/docusaurus.config.ts 不存在，无法同步博客顶部导航。",
                code="docusaurus_config_missing",
            )
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.upsert_blog_nav_item(content, slug, label)
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def replace_blog_nav_item(self, old_slug: str, new_slug: str, label: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.replace_blog_nav_item(content, old_slug, new_slug, label)
        if updated is None:
            updated = self.nav.upsert_blog_nav_item(content, new_slug, label)
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")

    def remove_blog_nav_item(self, slug: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        updated = self.nav.remove_blog_nav_item(content, slug)
        if updated is None:
            return
        if updated != content:
            settings.docusaurus_config_path.write_text(updated, encoding="utf-8")
