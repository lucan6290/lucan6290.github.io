"""Article-to-category index synchronization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_service import CategoryService


class ArticleCategoryIndexSyncService:
    """Keep docs top category index pages in sync with article changes."""

    def __init__(
        self,
        *,
        category: CategoryService | None = None,
        category_index: CategoryIndexService | None = None,
    ) -> None:
        self.category = category or CategoryService()
        self.category_index = category_index or CategoryIndexService()

    def preview_changes(self, relative_paths: list[str]) -> list[FileChangeDTO]:
        changes: list[FileChangeDTO] = []
        for top_slug in self.top_slugs_from_relative_paths(relative_paths):
            index_path = settings.docs_dir / top_slug / "index.md"
            if not index_path.exists():
                continue
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.project_relative_posix_path(index_path),
                    description="同步 docs 一级分类目录页",
                )
            )
        return changes

    def upsert_doc_link(self, relative_path: str, frontmatter: dict[str, Any]) -> None:
        title = self.string_value(frontmatter.get("title")) or Path(relative_path).stem
        category_path = [part for part in relative_path.replace("\\", "/").split("/")[:-1] if part]
        category_labels = self.category_labels_for_path(category_path)
        self.category_index.upsert_doc_link_if_index_exists(
            relative_path,
            title,
            category_labels,
            create_index=False,
        )

    def category_labels_for_path(self, category_path: list[str]) -> list[str]:
        labels: list[str] = []
        for index in range(1, len(category_path) + 1):
            current_path = category_path[:index]
            _path, label = self.category.resolve_article_category(ArticleType.docs, current_path)
            labels.append(label)
        return labels

    @staticmethod
    def top_slugs_from_relative_paths(relative_paths: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for relative_path in relative_paths:
            parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
            if len(parts) < 2:
                continue
            if len(parts) == 2 and parts[1].lower() in {"index.md", "index.mdx"}:
                continue
            top_slug = parts[0]
            if top_slug not in seen:
                seen.add(top_slug)
                result.append(top_slug)
        return result

    @staticmethod
    def project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
