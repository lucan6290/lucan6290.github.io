from __future__ import annotations

from pydantic import BaseModel


class GitCommitRequest(BaseModel):
    message: str
    filePath: str | None = None

