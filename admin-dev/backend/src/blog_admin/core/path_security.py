from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

from .errors import InvalidPathError


def decode_path(value: str) -> str:
    for _ in range(2):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded
    return value


def resolve_under(root: Path, relative_path: str, *, label: str = "路径") -> Path:
    decoded = decode_path(relative_path).replace("\\", "/")
    if not decoded or "://" in decoded:
        raise InvalidPathError(f"非法{label}", details={"path": relative_path})
    candidate = Path(decoded)
    if candidate.is_absolute():
        raise InvalidPathError(f"非法{label}", details={"path": relative_path})
    root_resolved = root.resolve()
    target = (root_resolved / candidate).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise InvalidPathError(f"非法{label}", details={"path": relative_path}) from exc
    return target

