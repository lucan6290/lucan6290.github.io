"""Image directory helpers for moved articles."""

from __future__ import annotations

import shutil
from pathlib import Path


class ArticleMoveImageService:
    """Handle same-name image directories during article moves."""

    @staticmethod
    def image_dir_for(article_path: Path) -> Path:
        return article_path.with_name(f"{article_path.stem}-imgs")

    @staticmethod
    def replace_dir_refs(body: str, old_dir_name: str, new_dir_name: str) -> str:
        if old_dir_name == new_dir_name:
            return body

        replacements = {
            f"./{old_dir_name}/": f"./{new_dir_name}/",
            f"{old_dir_name}/": f"{new_dir_name}/",
        }
        updated = body
        for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            updated = updated.replace(old, new)
        return updated

    @staticmethod
    def move_dir(source: Path, target: Path) -> None:
        shutil.move(str(source), str(target))
