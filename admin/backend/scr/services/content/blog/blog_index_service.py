"""Service for maintaining ``site/blog/index.md``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


@dataclass(frozen=True)
class BlogIndexPost:
    title: str
    to: str
    date: str


class BlogIndexService:
    """Maintain the root blog index without creating category ``index.md`` files."""

    category_list_heading = "## 分类目录"
    legacy_category_list_headings = ("## 鍒嗙被鐩綍",)

    def __init__(self) -> None:
        self.category = CategoryService()
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()

    def sync_all(self, *, dry_run: bool = True, confirm: bool = False) -> MutationPlanDTO:
        """Rebuild the blog root index from the real one-level categories and posts."""
        desired_by_path: dict[Path, str] = {}
        changes: list[FileChangeDTO] = []

        root_path = settings.blog_dir / "index.md"
        root_desired = self._build_root_index_content(root_path)
        root_action = "update" if root_path.exists() else "create"
        if not root_path.exists() or root_path.read_text(encoding="utf-8") != root_desired:
            desired_by_path[root_path] = root_desired
            changes.append(
                FileChangeDTO(
                    action=root_action,
                    target=self._project_relative_posix_path(root_path),
                    description=f"{'更新' if root_action == 'update' else '创建'} blog 总目录页",
                )
            )

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=[],
        )
        if dry_run:
            return plan
        if not confirm:
            raise BadRequestError("同步 blog 目录页需要显式确认。", code="confirmation_required")

        for path, content in desired_by_path.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return plan

    def _build_root_index_content(self, index_path: Path) -> str:
        categories = self._top_categories()
        if index_path.exists():
            parsed = self.markdown.parse(index_path.read_text(encoding="utf-8"))
            body_prefix = self._body_prefix_before_any_marker(
                parsed.body,
                (self.category_list_heading, *self.legacy_category_list_headings),
                "博客",
            )
        else:
            body_prefix = "# 博客\n\n这里用于整理个人表达、阶段观察、感想复盘和年度回顾。\n\n"

        body = f"{body_prefix.rstrip()}\n\n{self.category_list_heading}\n"
        posts_by_category = self._posts_by_top_category()
        for category in categories:
            body += f"\n### [{category.label}](/blog/{category.slug})\n"
            if category.description:
                body += f"\n{category.description}\n"
            posts = posts_by_category.get(category.slug, [])
            if posts:
                for post in posts:
                    body += f"\n- [{post.title}]({post.to})"
            else:
                body += "\n- 暂无文章"
            body += "\n"
        body += "\n"
        return body

    def _top_categories(self) -> list[CategoryDTO]:
        categories = self.category.list_categories(
            article_type=ArticleType.blog,
            include_empty=True,
            include_counts=True,
        )
        return sorted(
            [
                category
                for category in categories
                if len(category.path) == 1
                and (settings.blog_dir / category.path[0]).is_dir()
            ],
            key=lambda item: item.path[0],
        )

    def _posts_by_top_category(self) -> dict[str, list[BlogIndexPost]]:
        grouped: dict[str, list[BlogIndexPost]] = {}
        for path in self.filesystem.scan_article_files(ArticleType.blog):
            relative = self.filesystem.relative_posix_path(ArticleType.blog, path)
            parts = [part for part in relative.split("/") if part]
            if len(parts) < 2:
                continue
            parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
            frontmatter = parsed.frontmatter
            slug = str(frontmatter.get("slug") or path.stem).strip().lstrip("/") or path.stem
            grouped.setdefault(parts[0], []).append(
                BlogIndexPost(
                    title=str(frontmatter.get("title") or path.stem),
                    to=f"/blog/{slug}",
                    date=str(frontmatter.get("date") or ""),
                )
            )
        return {
            category: sorted(posts, key=lambda post: post.date, reverse=True)
            for category, posts in grouped.items()
        }

    @staticmethod
    def _body_prefix_before_any_marker(body: str, markers: tuple[str, ...], fallback_label: str) -> str:
        normalized = body.replace("\r\n", "\n")
        marker_indexes = [
            marker_index
            for marker in markers
            for marker_index in [normalized.find(marker)]
            if marker_index >= 0
        ]
        if marker_indexes:
            return normalized[: min(marker_indexes)]
        if normalized.strip():
            return normalized.rstrip() + "\n\n"
        return f"# {fallback_label}\n\n"

    @staticmethod
    def _project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
