from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ErrorPayload:
    code: str
    message: str
    details: Any = None


class AppError(Exception):
    """Application error mapped to the public API error envelope."""

    def __init__(self, code: str, message: str, *, status_code: int = 400, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


class InvalidPathError(AppError):
    def __init__(self, message: str = "非法路径", *, details: Any = None) -> None:
        super().__init__("INVALID_PATH", message, status_code=400, details=details)


class CommandRejectedError(AppError):
    def __init__(self, message: str = "命令被安全策略拒绝", *, details: Any = None) -> None:
        super().__init__("COMMAND_REJECTED", message, status_code=400, details=details)

