from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    text = content.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text

    match = re.search(r"^---\s*$", text[3:], flags=re.MULTILINE)
    if not match:
        return {}, text

    end = match.start() + 3
    yaml_text = text[3:end]
    body = text[match.end() + 3 :]
    if body.startswith("\r\n"):
        body = body[2:]
    elif body.startswith("\n"):
        body = body[1:]

    metadata = yaml.safe_load(yaml_text) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return dict(metadata), body


def flatten_categories(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        if not raw:
            return []
        if isinstance(raw[0], list):
            return [item for sub in raw for item in sub]
        return list(raw)
    return [str(raw)]


def _escape_yaml_value(value: str) -> str:
    if not value:
        return value
    special = r"""[:#\n\r\t{}[\],&*?|<>=!%@`"]"""
    if re.search(special, value) or value.startswith(" ") or value.endswith(" "):
        return f'"{value}"'
    return value


def generate_frontmatter(data: dict[str, Any]) -> str:
    lines: list[str] = ["---"]

    if data.get("title"):
        lines.append(f"title: {_escape_yaml_value(str(data['title']))}")
    if data.get("date"):
        lines.append(f"date: {data['date']}")
    if data.get("updated"):
        lines.append(f"updated: {data['updated']}")

    categories = data.get("categories")
    if categories:
        lines.append("")
        lines.append("categories:")
        if isinstance(categories, list) and categories:
            if isinstance(categories[0], list):
                for category in categories:
                    lines.append(f"  - [{', '.join(str(item) for item in category)}]")
            else:
                lines.append(f"  - [{', '.join(str(item) for item in categories)}]")

    tags = data.get("tags")
    if tags and len(tags) > 0:
        lines.append("")
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")

    optional_fields = [
        "description",
        "layout",
        "comments",
        "permalink",
        "excerpt",
        "published",
        "lang",
        "cover",
        "sticky",
        "slug",
        "status",
        "series",
    ]
    for field_name in optional_fields:
        value = data.get(field_name)
        if value is not None:
            lines.append("")
            if isinstance(value, str):
                lines.append(f"{field_name}: {_escape_yaml_value(value)}")
            else:
                lines.append(f"{field_name}: {value}")

    if data.get("series_order") is not None:
        lines.append(f"series_order: {data['series_order']}")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def get_asset_folder_path(article_path: str, posts_dir: Path) -> Path:
    return posts_dir / article_path.replace(".md", "")
