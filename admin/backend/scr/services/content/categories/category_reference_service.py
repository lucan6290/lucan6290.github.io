"""Category link reference helpers."""

from __future__ import annotations

from pathlib import Path

from scr.models.article import ArticleType
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class CategoryReferenceService:
    """Find and rewrite article references affected by category changes."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        sidebar: SidebarService | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.sidebar = sidebar or SidebarService()

    def category_link_replacements(
        self,
        article_type: ArticleType,
        old_category_path: list[str],
        new_category_path: list[str],
        article_files: list[Path],
        *,
        include_category_routes: bool = False,
    ) -> dict[str, str]:
        old_joined = "/".join(old_category_path)
        new_joined = "/".join(new_category_path)
        replacements = {
            old_joined: new_joined,
            f"./{old_joined}": f"./{new_joined}",
            f"../{old_joined}": f"../{new_joined}",
        }
        if include_category_routes:
            route_prefix = "/docs" if article_type == ArticleType.docs else "/blog"
            replacements.update(
                {
                    f"{route_prefix}/{old_joined}": f"{route_prefix}/{new_joined}",
                    f"{route_prefix.lstrip('/')}/{old_joined}": f"{route_prefix.lstrip('/')}/{new_joined}",
                }
            )
        if article_type == ArticleType.docs:
            replacements.update(
                {
                    f"/docs/{old_joined}": f"/docs/{new_joined}",
                    f"docs/{old_joined}": f"docs/{new_joined}",
                }
            )
            for article_path in article_files:
                old_relative_path = self.filesystem.relative_posix_path(article_type, article_path)
                new_relative_path = self.renamed_relative_path(
                    old_relative_path,
                    old_category_path,
                    new_category_path,
                )
                old_doc_id = self.sidebar.doc_id_from_relative_path(old_relative_path)
                new_doc_id = self.sidebar.doc_id_from_relative_path(new_relative_path)
                replacements.update(
                    {
                        old_relative_path: new_relative_path,
                        f"/docs/{old_doc_id}": f"/docs/{new_doc_id}",
                        f"docs/{old_doc_id}": f"docs/{new_doc_id}",
                    }
                )
        return {
            old: new
            for old, new in replacements.items()
            if old and new and old != new
        }

    def find_link_replacement_targets(self, replacements: dict[str, str]) -> list[str]:
        if not replacements:
            return []

        targets: list[str] = []
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                content = path.read_text(encoding="utf-8")
                if any(old in content for old in replacements):
                    targets.append(f"{current_type.value}:{self.filesystem.relative_posix_path(current_type, path)}")
        return targets

    def replace_article_links(self, replacements: dict[str, str]) -> None:
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                content = path.read_text(encoding="utf-8")
                updated = content
                for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
                    updated = updated.replace(old, new)
                if updated != content:
                    path.write_text(updated, encoding="utf-8")

    def find_external_article_references(self, article_type: ArticleType, deleted_articles: list[Path]) -> list[str]:
        candidates = self.deleted_article_reference_candidates(article_type, deleted_articles)
        if not candidates:
            return []

        deleted = {path.resolve() for path in deleted_articles}
        references: list[str] = []
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                if path.resolve() in deleted:
                    continue

                content = path.read_text(encoding="utf-8")
                if any(candidate in content for candidate in candidates):
                    references.append(f"{current_type.value}:{self.filesystem.relative_posix_path(current_type, path)}")
        return references

    def deleted_article_reference_candidates(self, article_type: ArticleType, deleted_articles: list[Path]) -> set[str]:
        candidates: set[str] = set()
        for article_path in deleted_articles:
            relative_path = self.filesystem.relative_posix_path(article_type, article_path)
            candidates.update({relative_path, f"./{relative_path}", f"../{relative_path}"})
            if article_type == ArticleType.docs:
                doc_id = self.sidebar.doc_id_from_relative_path(relative_path)
                candidates.update({doc_id, f"/docs/{doc_id}", f"docs/{doc_id}"})
        return {candidate for candidate in candidates if candidate}

    @staticmethod
    def renamed_relative_path(
        relative_path: str,
        old_category_path: list[str],
        new_category_path: list[str],
    ) -> str:
        parts = [part for part in Path(relative_path).as_posix().split("/") if part]
        return "/".join([*new_category_path, *parts[len(old_category_path) :]])
