from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from blog_admin.core.path_security import decode_path

from .repository import AssetRepository


def _is_external_src(src: str) -> bool:
    parsed = urlparse(src)
    return bool(parsed.scheme) or src.startswith(("/", "#", "data:", "blob:"))


def _normalize_asset_ref(src: str) -> str | None:
    src = decode_path(src.strip().strip("<>").strip("\"'"))
    if not src or _is_external_src(src):
        return None

    src = src.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    if not src:
        return None
    return Path(src).name


def extract_referenced_image_names(markdown: str) -> set[str]:
    refs: set[str] = set()

    patterns = [
        r"!\[[^\]]*]\(\s*(<[^>]+>|[^)\s]+)",
        r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>",
        r"\{%\s*asset_img\s+([^\s%]+)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, markdown, flags=re.IGNORECASE):
            ref = _normalize_asset_ref(match.group(1))
            if ref:
                refs.add(ref)

    return refs


class AssetReferenceScanner:
    def __init__(self, repository: AssetRepository) -> None:
        self.repository = repository

    def list_unused_images(self, article_path: str, markdown: str) -> list[dict]:
        referenced = extract_referenced_image_names(markdown)
        return [
            self.repository.image_info(path)
            for path in self.repository.list_article_images(article_path)
            if path.name not in referenced
        ]

    def delete_unused_images(self, article_path: str, markdown: str) -> list[dict]:
        referenced = extract_referenced_image_names(markdown)
        deleted: list[dict] = []

        for path in self.repository.list_article_images(article_path):
            if path.name in referenced:
                continue

            info = self.repository.image_info(path)
            path.unlink()
            deleted.append(info)

        return deleted
