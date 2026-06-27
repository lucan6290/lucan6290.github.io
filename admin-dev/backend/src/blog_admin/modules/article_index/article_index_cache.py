"""Readable, rebuildable local article index cache."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blog_admin.core.settings import settings

from .article_scanner import DRAFTS_DIR, POSTS_DIR, content_hash, scan_articles

CACHE_DIR = settings.cache_dir
INDEX_PATH = CACHE_DIR / "article-index.json"
CHUNKS_PATH = CACHE_DIR / "article-chunks.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(path)


def _markdown_files(include_drafts: bool) -> list[Path]:
    roots = [POSTS_DIR]
    if include_drafts:
        roots.append(DRAFTS_DIR)
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.md") if not (path.name == "index.md" and path.parent == POSTS_DIR))
    return files


def is_cache_fresh(index_data: dict[str, Any] | None, include_drafts: bool) -> bool:
    if not index_data or index_data.get("schemaVersion") != "1.0":
        return False
    articles = index_data.get("articles")
    if not isinstance(articles, list):
        return False
    indexed_hashes = {
        item.get("path"): item.get("contentHash")
        for item in articles
        if isinstance(item, dict)
    }
    indexed_paths = set(indexed_hashes)
    actual_paths = set()
    for path in _markdown_files(include_drafts):
        try:
            if path.is_relative_to(POSTS_DIR):
                relative = path.relative_to(POSTS_DIR).as_posix()
            else:
                relative = path.relative_to(DRAFTS_DIR).as_posix()
        except Exception:
            continue
        actual_paths.add(relative)
        try:
            if indexed_hashes.get(relative) != content_hash(path.read_text(encoding="utf-8")):
                return False
        except Exception:
            return False
    return indexed_paths == actual_paths


def scan_and_store(include_drafts: bool = True) -> dict[str, Any]:
    scanned = scan_articles(include_drafts=include_drafts)
    index_data = {
        "schemaVersion": scanned["schemaVersion"],
        "scannedAt": scanned["scannedAt"],
        "root": str(POSTS_DIR.parent),
        "articles": scanned["articles"],
        "failedFiles": scanned["failedFiles"],
        "stats": scanned["stats"],
    }
    chunks_data = {
        "schemaVersion": scanned["schemaVersion"],
        "scannedAt": scanned["scannedAt"],
        "chunks": scanned["chunks"],
    }
    _write_json_atomic(INDEX_PATH, index_data)
    _write_json_atomic(CHUNKS_PATH, chunks_data)
    return {**index_data, "chunks": scanned["chunks"], "indexStatus": "rebuilt"}


def load_or_scan(include_drafts: bool = True, force: bool = False) -> dict[str, Any]:
    index_data = _load_json(INDEX_PATH)
    chunks_data = _load_json(CHUNKS_PATH)
    if force or not is_cache_fresh(index_data, include_drafts) or not chunks_data:
        return scan_and_store(include_drafts=include_drafts)
    assert index_data is not None
    return {
        **index_data,
        "chunks": chunks_data.get("chunks", []),
        "indexStatus": "fresh",
    }
