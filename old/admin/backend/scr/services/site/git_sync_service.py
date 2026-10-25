"""GitHub 同步与仓库级 SSH 配置服务。"""

from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError
from scr.schemas.git_sync import (
    GitCommandResultDTO,
    GitPullRequestDTO,
    GitRemoteUpdateDTO,
    GitSshKeyCreateDTO,
    GitSyncStatusDTO,
)


@dataclass(frozen=True)
class _CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        parts = [self.stdout.rstrip(), self.stderr.rstrip()]
        return "\n".join(part for part in parts if part).strip()


class GitSyncService:
    """提供 GitHub Deploy Key 配置和服务器工作区同步能力。"""

    git_timeout_seconds = 300
    ssh_timeout_seconds = 30
    build_timeout_seconds = 600

    def __init__(self) -> None:
        self._lock = threading.Lock()

    @property
    def key_path(self) -> Path:
        return Path.home() / ".ssh" / "xiaocancoding_github_deploy"

    @property
    def public_key_path(self) -> Path:
        return self.key_path.with_suffix(self.key_path.suffix + ".pub")

    def get_status(self) -> GitSyncStatusDTO:
        """读取当前仓库与 SSH key 状态。"""
        status = self._run_git(["git", "status", "--porcelain"])
        changes = status.output.splitlines() if status.returncode == 0 and status.output else []
        remote_url = self._read_git_value(["git", "remote", "get-url", "origin"])
        return GitSyncStatusDTO(
            current_branch=self._read_git_value(["git", "branch", "--show-current"]) or "",
            remote_url=remote_url,
            git_user_name=self._read_git_value(["git", "config", "user.name"]),
            git_user_email=self._read_git_value(["git", "config", "user.email"]),
            ssh_key_path=str(self.key_path),
            public_key=self._read_public_key(),
            has_private_key=self.key_path.exists(),
            remote_uses_ssh=bool(remote_url and remote_url.startswith("git@github.com:")),
            is_dirty=bool(changes),
            changes=changes,
        )

    def create_ssh_key(self, payload: GitSshKeyCreateDTO) -> GitCommandResultDTO:
        """生成仓库专用 SSH Deploy Key，并配置当前仓库使用该 key。"""
        logs: list[str] = []
        ssh_dir = self.key_path.parent
        ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        if self.key_path.exists() and not payload.overwrite:
            logs.append(f"SSH key 已存在：{self.key_path}")
            self._configure_ssh_command(logs)
            return GitCommandResultDTO(status="success", logs=self._join_logs(logs))

        if payload.overwrite:
            for path in (self.key_path, self.public_key_path):
                if path.exists():
                    path.unlink()
                    logs.append(f"已删除旧文件：{path}")

        email = payload.email or "xiaocancoding-deploy-key"
        keygen = self._run_logged(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                email,
                "-f",
                str(self.key_path),
                "-N",
                "",
            ],
            logs,
            timeout=self.ssh_timeout_seconds,
        )
        if keygen.returncode != 0:
            return self._failed(logs, "ssh_keygen_failed", "生成 SSH key 失败。")

        self._chmod_private_key(logs)
        self._configure_ssh_command(logs)
        logs.append("请将上方公钥添加到 GitHub 仓库 Settings -> Deploy keys，并勾选 Allow write access。")
        return GitCommandResultDTO(status="success", logs=self._join_logs(logs))

    def update_remote(self, payload: GitRemoteUpdateDTO) -> GitCommandResultDTO:
        """更新 origin 地址。"""
        logs: list[str] = []
        if not self._is_supported_remote(payload.remote_url):
            return self._failed(logs, "remote_url_invalid", "仅支持 GitHub SSH 地址或 HTTPS 地址。")

        result = self._run_git_logged(["git", "remote", "set-url", "origin", payload.remote_url], logs)
        if result.returncode != 0:
            return self._failed(logs, "git_remote_set_url_failed", "更新 origin 地址失败。")

        if payload.remote_url.startswith("git@github.com:") and self.key_path.exists():
            self._configure_ssh_command(logs)
        return GitCommandResultDTO(status="success", logs=self._join_logs(logs))

    def test_ssh(self) -> GitCommandResultDTO:
        """测试当前服务器是否能通过 SSH 连接 GitHub。"""
        logs: list[str] = []
        command = ["ssh"]
        if self.key_path.exists():
            command.extend(["-i", str(self.key_path), "-o", "IdentitiesOnly=yes"])
        command.extend([
            "-T",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "git@github.com",
        ])
        result = self._run_logged(command, logs, timeout=self.ssh_timeout_seconds)
        output = result.output.lower()
        if "successfully authenticated" in output:
            return GitCommandResultDTO(status="success", logs=self._join_logs(logs))
        return self._failed(logs, "github_ssh_test_failed", "GitHub SSH 连接测试失败，请确认 Deploy Key 已添加并允许写入。")

    def pull(self, payload: GitPullRequestDTO) -> GitCommandResultDTO:
        """从 GitHub 拉取指定分支，更新服务器工作区。"""
        if not self._lock.acquire(blocking=False):
            raise ConflictError("已有 Git 同步任务运行中。", code="git_sync_running")

        logs: list[str] = []
        branch = payload.branch.strip()
        try:
            self._validate_branch(branch)

            dirty = self._run_git_logged(["git", "status", "--porcelain"], logs)
            if dirty.returncode != 0:
                return self._failed(logs, "git_status_failed", "读取 Git 状态失败。", branch=branch)
            if dirty.output:
                logs.append("当前工作区存在未提交变更，已停止拉取：")
                logs.append(dirty.output)
                return self._failed(logs, "dirty_worktree", "服务器存在未提交变更，请先发布或手动处理后再拉取。", branch=branch)

            fetch = self._run_git_logged(["git", "fetch", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"], logs)
            if fetch.returncode != 0:
                return self._failed(logs, "git_fetch_failed", "拉取远端分支状态失败。", branch=branch)

            if self._local_branch_exists(branch):
                switch = self._run_git_logged(["git", "switch", branch], logs)
            else:
                switch = self._run_git_logged(["git", "switch", "-c", branch, "--track", f"origin/{branch}"], logs)
            if switch.returncode != 0:
                return self._failed(logs, "git_switch_failed", "切换目标分支失败。", branch=branch)

            merge_args = ["git", "merge", "--ff-only", f"origin/{branch}"]
            if payload.mode == "rebase":
                merge_args = ["git", "rebase", f"origin/{branch}"]
            update = self._run_git_logged(merge_args, logs)
            if update.returncode != 0:
                if payload.mode == "rebase":
                    abort = self._run_git_logged(["git", "rebase", "--abort"], logs, log_nonzero=False)
                    if abort.returncode == 0:
                        logs.append("已自动执行 git rebase --abort。")
                return self._failed(logs, "git_update_failed", "更新服务器工作区失败，可能需要手动处理分支差异。", branch=branch)

            if payload.run_build_after:
                build = self._run_build(logs)
                if build.returncode != 0:
                    return self._failed(logs, "build_failed_after_pull", "拉取后构建失败。", branch=branch)

            return GitCommandResultDTO(status="success", branch=branch, logs=self._join_logs(logs))
        finally:
            self._lock.release()

    def _configure_ssh_command(self, logs: list[str]) -> None:
        ssh_command = f"ssh -i {self.key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
        result = self._run_git_logged(["git", "config", "core.sshCommand", ssh_command], logs)
        if result.returncode == 0:
            logs.append("已配置当前仓库使用服务器 Deploy Key。")

    def _chmod_private_key(self, logs: list[str]) -> None:
        if os.name == "nt":
            return
        try:
            self.key_path.chmod(0o600)
            self.public_key_path.chmod(0o644)
            logs.append("已设置 SSH key 文件权限。")
        except OSError as exc:
            logs.append(f"设置 SSH key 权限失败：{exc}")

    def _read_public_key(self) -> str | None:
        if not self.public_key_path.exists():
            return None
        return self.public_key_path.read_text(encoding="utf-8").strip()

    def _read_git_value(self, args: list[str]) -> str | None:
        result = self._run_git(args)
        if result.returncode != 0 or not result.output:
            return None
        return result.output.splitlines()[-1].strip()

    def _local_branch_exists(self, branch: str) -> bool:
        return self._run_git(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]).returncode == 0

    def _validate_branch(self, branch: str) -> None:
        if branch.startswith("-"):
            raise BadRequestError("目标分支名称不合法。", code="branch_invalid")
        result = self._run_git(["git", "check-ref-format", "--branch", branch])
        if result.returncode != 0:
            raise BadRequestError("目标分支名称不合法。", code="branch_invalid", details={"branch": branch})

    @staticmethod
    def _is_supported_remote(remote_url: str) -> bool:
        return remote_url.startswith("git@github.com:") or remote_url.startswith("https://github.com/")

    def _run_build(self, logs: list[str]) -> _CommandResult:
        command = ["cmd", "/c", "npm", "run", "build"] if os.name == "nt" else ["npm", "run", "build"]
        return self._run_logged(command, logs, cwd=settings.site_dir, timeout=self.build_timeout_seconds)

    def _run_git_logged(
        self,
        args: list[str],
        logs: list[str],
        *,
        log_nonzero: bool = True,
    ) -> _CommandResult:
        return self._run_logged(args, logs, cwd=settings.project_root, timeout=self.git_timeout_seconds, log_nonzero=log_nonzero)

    def _run_git(self, args: list[str]) -> _CommandResult:
        return self._run(args, cwd=settings.project_root, timeout=self.git_timeout_seconds)

    def _run_logged(
        self,
        args: list[str],
        logs: list[str],
        *,
        cwd=settings.project_root,
        timeout: int,
        log_nonzero: bool = True,
    ) -> _CommandResult:
        logs.append(f"$ {self._format_command(args)}")
        try:
            result = self._run(args, cwd=cwd, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            result = _CommandResult(
                args=args,
                returncode=124,
                stdout=self._decode_output(exc.stdout),
                stderr=self._decode_output(exc.stderr),
            )
            logs.append(f"命令超过 {timeout} 秒未完成。")
        except OSError as exc:
            result = _CommandResult(args=args, returncode=1, stdout="", stderr=str(exc))

        if result.output:
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
        return _CommandResult(args=args, returncode=result.returncode, stdout=result.stdout or "", stderr=result.stderr or "")

    @staticmethod
    def _failed(
        logs: list[str],
        code: str,
        message: str,
        *,
        branch: str | None = None,
    ) -> GitCommandResultDTO:
        return GitCommandResultDTO(
            status="failed",
            branch=branch,
            logs=GitSyncService._join_logs(logs),
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
