from __future__ import annotations

from ...core.response import ok
from ...core.settings import settings
from .audit import GitAuditLogger
from .schemas import GitCommitRequest
from .service import GitOpsService


class GitService:
    def __init__(self) -> None:
        self.service = GitOpsService(
            settings.repo_root,
            audit_logger=GitAuditLogger(settings.cache_dir / "gitops-audit.jsonl"),
        )

    async def commit(self, req: GitCommitRequest) -> dict:
        return ok(await self.service.commit(req))

    async def push(self) -> dict:
        return ok(await self.service.push())

    async def deploy(self, req: GitCommitRequest) -> dict:
        return ok(await self.service.deploy(req))


git_service = GitService()
