from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from .errors import CommandRejectedError
from .path_security import resolve_under


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str

    def to_frontend_dict(self) -> dict[str, str]:
        return {"stdout": self.stdout, "stderr": self.stderr}


class GitCommandPolicy:
    """Centralized policy for local git operations exposed by the admin API."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def validate_add_target(self, file_path: str | None) -> str:
        if not file_path:
            return self.audit_add_all()
        self._reject_unsafe_path_shape(file_path)
        target = resolve_under(self.repo_root, file_path, label="Git 文件路径")
        if target == self.repo_root:
            raise CommandRejectedError("不能将仓库根目录作为指定文件提交")
        return target.relative_to(self.repo_root).as_posix()

    def validate_args(self, args: Iterable[str]) -> tuple[str, ...]:
        safe_args = tuple(args)
        if not safe_args:
            raise CommandRejectedError("Git 命令不能为空")
        if any(arg == "" or "\x00" in arg for arg in safe_args):
            raise CommandRejectedError("Git 参数包含非法字符")
        self._validate_git_command_shape(safe_args)
        return safe_args

    def audit_add_all(self) -> str:
        # AUDIT: deploy without filePath intentionally keeps `git add .`
        # behavior for the current frontend. Narrow this once callers send
        # explicit changed paths.
        return "."

    @staticmethod
    def _reject_unsafe_path_shape(file_path: str) -> None:
        normalized = file_path.strip().replace("\\", "/")
        if not normalized:
            raise CommandRejectedError("Git 文件路径不能为空")

        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(file_path)
        if posix_path.is_absolute() or windows_path.is_absolute():
            raise CommandRejectedError("Git 文件路径不允许使用绝对路径")
        if windows_path.drive or windows_path.root:
            raise CommandRejectedError("Git 文件路径不允许使用驱动器或根路径")
        if any(part == ".." for part in posix_path.parts):
            raise CommandRejectedError("Git 文件路径不允许使用 .. 越权")

    @staticmethod
    def _validate_git_command_shape(args: tuple[str, ...]) -> None:
        command = args[0]
        if command == "add" and len(args) == 2:
            return
        if command == "commit" and len(args) == 3 and args[1] == "-m":
            return
        if command == "push" and args == ("push", "origin"):
            return
        raise CommandRejectedError("Git 命令不在允许列表中", details={"args": list(args)})

