from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from ...core.path_security import resolve_under
from ...core.settings import settings
from .frontmatter import flatten_categories, parse_frontmatter
from .schemas import PostStatus


def _safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    value = data.get(key, default)
    return default if value is None else value


class PostRepository:
    def __init__(self, posts_dir: Path = settings.posts_dir, blog_root: Path = settings.blog_root) -> None:
        self.posts_dir = posts_dir
        self.blog_root = blog_root
        self.category_map = self._load_category_map()

    def resolve_path(self, path: str) -> Path:
        return resolve_under(self.posts_dir, path, label="文章路径")

    def exists(self, path: str) -> bool:
        return self.resolve_path(path).exists()

    def read_raw(self, path: str) -> str:
        return self.resolve_path(path).read_text(encoding="utf-8")

    def write_raw(self, path: str, content: str) -> None:
        self.resolve_path(path).write_text(content, encoding="utf-8")

    def delete(self, path: str) -> None:
        full_path = self.resolve_path(path)
        full_path.unlink()
        asset_folder = full_path.with_suffix("")
        if asset_folder.exists() and asset_folder.is_dir():
            shutil.rmtree(asset_folder, ignore_errors=True)

    def list_markdown_files(self, directory: Path | None = None, base: Path | None = None) -> list[str]:
        directory = directory or self.posts_dir
        base = base or self.posts_dir
        results: list[str] = []
        if not directory.exists():
            return results

        for item in sorted(directory.iterdir()):
            if item.is_dir():
                if not item.with_suffix(".md").exists():
                    results.extend(self.list_markdown_files(item, base))
            elif item.suffix == ".md":
                results.append(item.relative_to(base).as_posix())
        return results

    def parse_post_summary(self, relative_path: str) -> dict[str, Any] | None:
        full_path = self.resolve_path(relative_path)
        if not full_path.exists():
            return None

        content = full_path.read_text(encoding="utf-8")
        front_matter, _ = parse_frontmatter(content)
        categories = flatten_categories(_safe_get(front_matter, "categories", []))
        tags = _safe_get(front_matter, "tags", []) or []
        status_value = _safe_get(front_matter, "status", PostStatus.PUBLISHED)
        if status_value not in ("draft", "wip", "published"):
            status_value = PostStatus.PUBLISHED

        primary_slug = self.to_slug(categories[0]) if categories else ""
        sub_slug = self.to_slug(categories[1]) if len(categories) > 1 else ""

        return {
            "title": _safe_get(front_matter, "title", ""),
            "filename": Path(relative_path).stem,
            "path": relative_path.replace("\\", "/"),
            "date": str(_safe_get(front_matter, "date", "")),
            "updated": _safe_get(front_matter, "updated"),
            "category": primary_slug,
            "subCategory": sub_slug,
            "categories": categories,
            "tags": tags if isinstance(tags, list) else [],
            "description": _safe_get(front_matter, "description"),
            "cover": _safe_get(front_matter, "cover"),
            "status": status_value,
            "series": _safe_get(front_matter, "series"),
            "seriesOrder": _safe_get(front_matter, "series_order"),
        }

    def to_slug(self, name: str) -> str:
        return self.category_map.get(name, name)

    def _load_category_map(self) -> dict[str, str]:
        try:
            config_path = self.blog_root / "_config.yml"
            with open(config_path, encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}
            return config.get("category_map", {}) or {}
        except Exception:
            return {}

