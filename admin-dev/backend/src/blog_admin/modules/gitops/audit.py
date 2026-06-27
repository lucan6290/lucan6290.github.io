from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class GitAuditLogger:
    """Append-only JSONL audit log for local Git operations."""

    def __init__(self, audit_log_path: Path) -> None:
        self.audit_log_path = audit_log_path

    def record(
        self,
        *,
        action: str,
        args: tuple[str, ...],
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        event: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "args": list(args),
            "status": status,
        }
        if details:
            event["details"] = details
        with self.audit_log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


class NullGitAuditLogger:
    def record(
        self,
        *,
        action: str,
        args: tuple[str, ...],
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        return None
