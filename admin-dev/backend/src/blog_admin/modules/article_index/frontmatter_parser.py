from __future__ import annotations

from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    content = content.lstrip("\ufeff")
    if not content.startswith("---"):
        return {}, content

    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, content

    end_index: int | None = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            end_index = idx
            break
    if end_index is None:
        return {}, content

    metadata_text = "".join(lines[1:end_index])
    body = "".join(lines[end_index + 1:])
    metadata = yaml.safe_load(metadata_text) or {}
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
            return [str(item) for sub in raw for item in sub]
        return [str(item) for item in raw]
    return [str(raw)]
