from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

from blog_admin.core.command_policy import CommandResult, GitCommandPolicy
from blog_admin.core.errors import AppError

from .audit import NullGitAuditLogger
from .schemas import GitCommitRequest


class GitOpsError(AppError):
    """Application-level GitOps failure safe to surface as an API error."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__("GIT_OPS_ERROR", message, status_code=200, details=details)


class GitAuditLoggerProtocol(Protocol):
    def record(
        self,
        *,
        action: str,
        args: tuple[str, ...],
        status: str,
        details: dict | None = None,
    ) -> None: ...


class GitCommandRunnerProtocol(Protocol):
    async def run(self, *args: str) -> CommandResult: ...


class GitCommandRunner:
    """Async Git command runner kept below the application-service boundary."""

    def __init__(
        self,
        repo_root: Path,
        policy: GitCommandPolicy | None = None,
        audit_logger: GitAuditLoggerProtocol | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.policy = policy or GitCommandPolicy(self.repo_root)
        self.audit_logger = audit_logger or NullGitAuditLogger()

    async def run(self, *args: str) -> CommandResult:
        raw_args = tuple(args)
        try:
            safe_args = self.policy.validate_args(raw_args)
        except AppError as exc:
            self.audit_logger.record(
                action="git",
                args=raw_args,
                status="rejected",
                details={"code": exc.code, "message": exc.message},
            )
            raise
        self.audit_logger.record(action="git", args=safe_args, status="started")
        proc = await asyncio.create_subprocess_exec(
            "git",
            *safe_args,
            cwd=str(self.repo_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            rendered_args = " ".join(safe_args)
            self.audit_logger.record(
                action="git",
                args=safe_args,
                status="failed",
                details={"returnCode": proc.returncode, "stdout": stdout, "stderr": stderr},
            )
            raise GitOpsError(
                f"git {rendered_args} 失败",
                details={"returnCode": proc.returncode, "stdout": stdout, "stderr": stderr},
            )

        self.audit_logger.record(action="git", args=safe_args, status="succeeded")
        return CommandResult(stdout=stdout, stderr=stderr)


class GitOpsService:
    """Application service for commit, push, and deploy workflows."""

    def __init__(
        self,
        repo_root: Path,
        runner: GitCommandRunnerProtocol | None = None,
        policy: GitCommandPolicy | None = None,
        audit_logger: GitAuditLoggerProtocol | None = None,
    ) -> None:
        self.policy = policy or GitCommandPolicy(repo_root)
        self.runner = runner or GitCommandRunner(repo_root, self.policy, audit_logger)

    async def commit(self, request: GitCommitRequest) -> dict[str, str]:
        message = self._require_message(request.message)
        await self.runner.run("add", self.policy.validate_add_target(request.filePath))
        result = await self.runner.run("commit", "-m", message)
        return result.to_frontend_dict()

    async def push(self) -> dict[str, str]:
        result = await self.runner.run("push", "origin")
        return result.to_frontend_dict()

    async def deploy(self, request: GitCommitRequest) -> dict[str, dict[str, str]]:
        message = self._require_message(request.message)
        await self.runner.run("add", self.policy.validate_add_target(request.filePath))
        commit_result = await self.runner.run("commit", "-m", message)
        push_result = await self.runner.run("push", "origin")
        return {
            "commit": commit_result.to_frontend_dict(),
            "push": push_result.to_frontend_dict(),
        }

    @staticmethod
    def _require_message(message: str) -> str:
        cleaned = (message or "").strip()
        if not cleaned:
            raise AppError("VALIDATION_ERROR", "提交信息不能为空", status_code=200)
        return cleaned
