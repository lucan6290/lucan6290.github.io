"""站点发布服务。"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.schemas.deploy import DeployRequestDTO, DeployResultDTO


@dataclass(frozen=True)
class _CommandResult:
    args: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        parts = [self.stdout.rstrip(), self.stderr.rstrip()]
        return "\n".join(part for part in parts if part).strip()


class DeployService:
    """执行构建、提交和推送发布流程。"""

    build_timeout_seconds = 600
    git_timeout_seconds = 300

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def run_deploy(self, payload: DeployRequestDTO) -> DeployResultDTO:
        """同步执行发布流程并返回完整日志。"""
        if not self._lock.acquire(blocking=False):
            raise ConflictError("已有发布任务运行中。", code="deploy_task_running")

        logs: list[str] = []
        branch = payload.branch.strip()

        try:
            self._validate_branch(branch)

            status = self._run_git(["git", "status", "--porcelain"], logs=logs)
            if status.returncode != 0:
                return self._failed(branch, logs, "git_status_failed", "读取 Git 状态失败。")
            if not status.output:
                logs.append("没有可发布的变更。")
                return DeployResultDTO(status="no_changes", branch=branch, logs=self._join_logs(logs))

            if payload.run_build_first:
                if payload.clean_build:
                    self._clean_build_dir(logs)
                build = self._run_build(logs)
                if build.returncode != 0:
                    return self._failed(branch, logs, "build_failed", "构建失败，已停止发布。")

            add = self._run_git(["git", "add", "-A"], logs=logs)
            if add.returncode != 0:
                return self._failed(branch, logs, "git_add_failed", "暂存变更失败。")

            diff = self._run_git(
                ["git", "diff", "--cached", "--quiet"],
                logs=logs,
                log_output=False,
                log_nonzero=False,
            )
            if diff.returncode == 0:
                logs.append("没有需要提交的暂存内容。")
                return DeployResultDTO(status="no_changes", branch=branch, logs=self._join_logs(logs))
            if diff.returncode != 1:
                return self._failed(branch, logs, "git_diff_failed", "检查暂存内容失败。")

            commit = self._run_git(["git", "commit", "-m", payload.commit_message], logs=logs)
            if commit.returncode != 0:
                return self._failed(branch, logs, "git_commit_failed", "提交失败。")

            rev = self._run_git(["git", "rev-parse", "HEAD"], logs=logs)
            if rev.returncode != 0 or not rev.output:
                return self._failed(branch, logs, "git_rev_parse_failed", "读取提交哈希失败。")
            commit_hash = rev.output.splitlines()[-1].strip()

            push = self._run_git(["git", "push", "origin", f"HEAD:{branch}"], logs=logs)
            if push.returncode != 0:
                return self._failed(branch, logs, "git_push_failed", "推送失败。", commit=commit_hash)

            return DeployResultDTO(
                status="success",
                branch=branch,
                commit=commit_hash,
                pushed=True,
                logs=self._join_logs(logs),
            )
        finally:
            self._lock.release()

    def _validate_branch(self, branch: str) -> None:
        if branch.startswith("-"):
            raise BadRequestError("目标分支名称不合法。", code="branch_invalid")

        result = self._run(
            ["git", "check-ref-format", "--branch", branch],
            cwd=settings.project_root,
            timeout=self.git_timeout_seconds,
        )
        if result.returncode != 0:
            raise BadRequestError(
                "目标分支名称不合法。",
                code="branch_invalid",
                details={"branch": branch, "stderr": result.stderr.strip()},
            )

    def _run_build(self, logs: list[str]) -> _CommandResult:
        command = ["cmd", "/c", "npm", "run", "build"] if os.name == "nt" else ["npm", "run", "build"]
        return self._run_logged(command, cwd=settings.site_dir, logs=logs, timeout=self.build_timeout_seconds)

    def _run_git(
        self,
        args: list[str],
        *,
        logs: list[str],
        log_output: bool = True,
        log_nonzero: bool = True,
    ) -> _CommandResult:
        return self._run_logged(
            args,
            cwd=settings.project_root,
            logs=logs,
            timeout=self.git_timeout_seconds,
            log_output=log_output,
            log_nonzero=log_nonzero,
        )

    def _run_logged(
        self,
        args: list[str],
        *,
        cwd,
        logs: list[str],
        timeout: int,
        log_output: bool = True,
        log_nonzero: bool = True,
    ) -> _CommandResult:
        logs.append(f"$ {self._format_command(args)}")
        try:
            result = self._run(args, cwd=cwd, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout = self._decode_output(exc.stdout)
            stderr = self._decode_output(exc.stderr)
            result = _CommandResult(args=args, cwd=str(cwd), returncode=124, stdout=stdout, stderr=stderr)
            logs.append(f"命令超过 {timeout} 秒未完成。")
        except OSError as exc:
            result = _CommandResult(args=args, cwd=str(cwd), returncode=1, stdout="", stderr=str(exc))

        if log_output and result.output:
            logs.append(result.output)
        if log_nonzero and result.returncode != 0:
            logs.append(f"命令退出码：{result.returncode}")
        return result

    @staticmethod
    def _run(args: list[str], *, cwd, timeout: int) -> _CommandResult:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return _CommandResult(
            args=args,
            cwd=str(cwd),
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
        )

    def _clean_build_dir(self, logs: list[str]) -> None:
        build_dir = settings.site_dir / "build"
        try:
            safe_build_dir = ensure_child_path(settings.site_dir, build_dir)
        except PathSecurityError as exc:
            raise BadRequestError("构建目录路径越界，已拒绝清理。", code="build_dir_invalid") from exc

        logs.append("$ clean site/build")
        if safe_build_dir.exists():
            shutil.rmtree(safe_build_dir)
            logs.append("已清理 site/build。")
        else:
            logs.append("site/build 不存在，跳过清理。")

    @staticmethod
    def _failed(
        branch: str,
        logs: list[str],
        code: str,
        message: str,
        *,
        commit: str | None = None,
    ) -> DeployResultDTO:
        return DeployResultDTO(
            status="failed",
            branch=branch,
            commit=commit,
            pushed=False,
            logs=DeployService._join_logs(logs),
            error={"code": code, "message": message},
        )

    @staticmethod
    def _format_command(args: list[str]) -> str:
        return " ".join(f'"{arg}"' if " " in arg else arg for arg in args)

    @staticmethod
    def _decode_output(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value or ""

    @staticmethod
    def _join_logs(logs: list[str]) -> str:
        return "\n\n".join(log.strip() for log in logs if log and log.strip())
