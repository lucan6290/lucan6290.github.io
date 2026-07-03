"""Article link reference helpers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from scr.models.article import ArticleType
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleReferenceService:
    """Find and rewrite explicit article references in markdown files."""

    date_slug_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        sidebar: SidebarService | None = None,
        summary: ArticleSummaryService | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.sidebar = sidebar or SidebarService()
        self.summary = summary

    def moved_article_link_replacements(
        self,
        article_type: ArticleType,
        old_relative_path: str,
        new_relative_path: str,
        old_frontmatter: dict[str, Any],
        new_frontmatter: dict[str, Any],
    ) -> dict[str, str]:
        old_slug = self.resolve_slug(article_type, old_relative_path, old_frontmatter)
        new_slug = self.resolve_slug(article_type, new_relative_path, new_frontmatter)
        old_route = self.build_route(article_type, old_slug)
        new_route = self.build_route(article_type, new_slug)
        replacements = {
            old_route: new_route,
            old_route.lstrip("/"): new_route.lstrip("/"),
            old_relative_path: new_relative_path,
            f"./{old_relative_path}": f"./{new_relative_path}",
            f"../{old_relative_path}": f"../{new_relative_path}",
        }
        return {old: new for old, new in replacements.items() if old and new and old != new}

    def find_replacement_target_paths(
        self,
        replacements: dict[str, str],
        *,
        exclude_path: Path | None = None,
    ) -> list[Path]:
        if not replacements:
            return []

        excluded = exclude_path.resolve() if exclude_path else None
        targets: list[Path] = []
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                if excluded and path.resolve() == excluded:
                    continue
                content = path.read_text(encoding="utf-8")
                if any(old in content for old in replacements):
                    targets.append(path)
        return targets

    def replace_article_links(
        self,
        replacements: dict[str, str],
        *,
        exclude_path: Path | None = None,
    ) -> None:
        for path in self.find_replacement_target_paths(replacements, exclude_path=exclude_path):
            content = path.read_text(encoding="utf-8")
            updated = content
            for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
                updated = updated.replace(old, new)
            if updated != content:
                path.write_text(updated, encoding="utf-8")

    def find_article_references(
        self,
        article_type: ArticleType,
        relative_path: str,
        candidates: set[str],
    ) -> list[str]:
        if not candidates:
            return []

        references: list[str] = []
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                current_relative_path = self.filesystem.relative_posix_path(current_type, path)
                if current_type == article_type and current_relative_path == relative_path:
                    continue

                content = path.read_text(encoding="utf-8")
                if any(candidate in content for candidate in candidates):
                    references.append(f"{current_type.value}:{current_relative_path}")
        return references

    def article_reference_candidates(
        self,
        article_type: ArticleType,
        relative_path: str,
        frontmatter: dict[str, Any],
    ) -> set[str]:
        candidates = {relative_path, f"./{relative_path}", f"../{relative_path}"}
        if article_type == ArticleType.docs:
            doc_id = self.sidebar.doc_id_from_relative_path(relative_path)
            candidates.update({doc_id, f"/docs/{doc_id}", f"docs/{doc_id}"})
        else:
            slug = self.resolve_slug(article_type, relative_path, frontmatter)
            candidates.update({f"/blog/{slug}", f"blog/{slug}"})
        return {candidate for candidate in candidates if candidate}

    def resolve_slug(self, article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> str:
        if self.summary is not None:
            return self.summary.resolve_slug(article_type, relative_path, frontmatter)
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
        if article_type == ArticleType.docs:
            return f"/docs/{slug}"
        return f"/blog/{slug}"

    @staticmethod
    def string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
