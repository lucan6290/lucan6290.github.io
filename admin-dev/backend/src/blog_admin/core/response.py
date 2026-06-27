from __future__ import annotations

from typing import Any


def ok(data: Any = None) -> dict[str, Any]:
    return {"success": True, "data": data}


def fail(code: str, message: str, *, details: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"success": False, "error": error}


