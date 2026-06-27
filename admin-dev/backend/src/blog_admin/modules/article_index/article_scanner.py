"""Local Markdown article scanner for knowledge QA."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from blog_admin.core.settings import settings

from .frontmatter_parser import flatten_categories, parse_frontmatter
from .schemas import ArticleChunk, ArticleIndexItem

DRAFTS_DIR = settings.blog_root / "source" / "_drafts"
POSTS_DIR = settings.posts_dir


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_categories(raw: Any) -> list[list[str]]:
    flat = flatten_categories(raw)
    if not flat:
        return []
    if len(flat) == 1:
        return [[flat[0]]]
    return [[flat[0], flat[1]]]


def _extract_headings(body: str) -> list[str]:
    return [
        line.strip()
        for line in body.splitlines()
        if re.match(r"^#{1,6}\s+\S", line.strip())
    ]


def _strip_markdown(body: str) -> str:
    text = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"^[#>\-\*\+\s]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _excerpt(body: str, max_len: int = 220) -> str:
    text = _strip_markdown(body)
    return text[:max_len]


def _parse_filename(path: Path) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    parts = path.stem.split("-", 2)
    if len(parts) != 3:
        warnings.append("文件名不符合 prefix1-prefix2-title.md 规则")
        return "", "", warnings
    prefix1, prefix2, _title = parts
    if prefix1 not in settings.prefix_to_dir:
        warnings.append(f"未知一级前缀: {prefix1}")
    if not prefix2 or "-" in prefix2:
        warnings.append("二级前缀非法")
    return prefix1, prefix2, warnings


def _iter_markdown_files(include_drafts: bool) -> list[Path]:
    roots = [POSTS_DIR]
    if include_drafts:
        roots.append(DRAFTS_DIR)
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            if path.name == "index.md" and path.parent == POSTS_DIR:
                continue
            files.append(path)
    return files


def _relative_article_path(path: Path) -> str:
    try:
        return path.relative_to(POSTS_DIR).as_posix()
    except ValueError:
        return path.relative_to(DRAFTS_DIR).as_posix()


def _chunk_article(path: str, title: str, body: str, hash_value: str) -> list[ArticleChunk]:
    chunks: list[ArticleChunk] = []
    lines = body.splitlines()
    current_heading: list[str] = []
    current_lines: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_lines, start_line
        text = "\n".join(current_lines).strip()
        if not text:
            current_lines = []
            start_line = end_line + 1
            return
        chunk_index = len(chunks) + 1
        chunks.append(ArticleChunk(
            id=f"{path}#{chunk_index}",
            articlePath=path,
            articleTitle=title,
            headingPath=current_heading.copy(),
            text=text,
            startLine=start_line,
            endLine=end_line,
            contentHash=hash_value,
        ))
        current_lines = []
        start_line = end_line + 1

    for idx, line in enumerate(lines, start=1):
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            flush(idx - 1)
            level = len(heading_match.group(1))
            current_heading[:] = current_heading[: level - 1] + [line.strip()]
            start_line = idx
        current_lines.append(line)
        if len("\n".join(current_lines)) >= 1200:
            flush(idx)
    flush(len(lines))
    return chunks


def scan_articles(include_drafts: bool = True) -> dict[str, Any]:
    articles: list[ArticleIndexItem] = []
    chunks: list[ArticleChunk] = []
    failed_files: list[dict[str, str]] = []

    for path in _iter_markdown_files(include_drafts):
        try:
            raw = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(raw)
            hash_value = content_hash(raw)
            relative = _relative_article_path(path)
            _prefix1, _prefix2, warnings = _parse_filename(path)
            categories = _normalize_categories(fm.get("categories"))
            raw_tags = fm.get("tags")
            tags: list[Any] = raw_tags if isinstance(raw_tags, list) else []
            status = fm.get("status")
            if status not in ("draft", "wip", "published"):
                status = None
            title = str(fm.get("title") or path.stem)
            item = ArticleIndexItem(
                path=relative,
                fileName=path.name,
                title=title,
                date=str(fm.get("date")) if fm.get("date") is not None else None,
                updated=str(fm.get("updated")) if fm.get("updated") is not None else None,
                categories=categories,
                tags=[str(tag) for tag in tags],
                status=status,
                published=fm.get("published") if isinstance(fm.get("published"), bool) else None,
                description=str(fm.get("description")) if fm.get("description") is not None else None,
                headings=_extract_headings(body),
                excerpt=_excerpt(body),
                mtime=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
                contentHash=hash_value,
                warnings=warnings,
            )
            articles.append(item)
            chunks.extend(_chunk_article(relative, title, body, hash_value))
        except Exception as exc:
            failed_files.append({"path": str(path), "error": str(exc)})

    return {
        "schemaVersion": "1.0",
        "scannedAt": now_iso(),
        "articles": [item.model_dump() for item in articles],
        "chunks": [chunk.model_dump() for chunk in chunks],
        "failedFiles": failed_files,
        "stats": build_stats(articles),
    }


def build_stats(articles: list[ArticleIndexItem]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    for article in articles:
        primary = article.categories[0][0] if article.categories and article.categories[0] else "未分类"
        by_category[primary] = by_category.get(primary, 0) + 1
        status = article.status or "unknown"
        by_status[status] = by_status.get(status, 0) + 1
        for tag in article.tags:
            by_tag[tag] = by_tag.get(tag, 0) + 1
    return {
        "total": len(articles),
        "byCategory": by_category,
        "byStatus": by_status,
        "byTag": by_tag,
    }
