"""Category filesystem helpers."""

from __future__ import annotations

from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.models.article import ArticleType
from scr.infrastructure.filesystem.filesystem_service import FileSystemService


class CategoryDirectoryService:
    """Resolve category directories and files below them."""

    def __init__(self, *, filesystem: FileSystemService | None = None) -> None:
        self.filesystem = filesystem or FileSystemService()

    def category_dir(self, article_type: ArticleType, path: list[str]) -> Path | None:
        root = settings.docs_dir if article_type == ArticleType.docs else settings.blog_dir
        try:
            return ensure_child_path(root, root.joinpath(*path))
        except PathSecurityError as exc:
            raise BadRequestError("分类路径越界，已拒绝访问。", code="path_out_of_scope") from exc

    def article_files_under_category(self, article_type: ArticleType, category_dir: Path | None) -> list[Path]:
        if not category_dir:
            return []

        resolved_category_dir = category_dir.resolve()
        return [
            article_path
            for article_path in self.filesystem.scan_article_files(article_type)
            if article_path.resolve().is_relative_to(resolved_category_dir)
        ]

    @staticmethod
    def project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
