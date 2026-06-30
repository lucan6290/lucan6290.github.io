"""站点构建服务。"""

import os
import shutil
import subprocess
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from scr.core.config import settings
from scr.core.exceptions import AppError, ConflictError, NotFoundError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.schemas.build import BuildRequestDTO, TaskDTO


class BuildService:
    """执行 Docusaurus 构建并记录任务状态。"""

    build_timeout_seconds = 600

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, TaskDTO] = {}

    def run_build(self, payload: BuildRequestDTO) -> TaskDTO:
        """同步执行构建验证，返回最终任务状态。"""
        if not self._lock.acquire(blocking=False):
            raise ConflictError("已有构建任务运行中。", code="build_task_running")

        task_id = self._new_task_id()
        task = TaskDTO(
            task_id=task_id,
            type="build",
            status="running",
            started_at=self._now_shanghai_iso(),
        )
        self._tasks[task_id] = task

        try:
            if payload.clean:
                self._clean_build_dir()

            result = subprocess.run(
                self._build_command(),
                cwd=settings.site_dir,
                capture_output=True,
                text=True,
                timeout=self.build_timeout_seconds,
                check=False,
            )
            logs = self._join_logs(result.stdout, result.stderr)
            if result.returncode == 0:
                task = task.model_copy(
                    update={
                        "status": "success",
                        "exit_code": result.returncode,
                        "finished_at": self._now_shanghai_iso(),
                        "logs": logs,
                    }
                )
            else:
                task = task.model_copy(
                    update={
                        "status": "failed",
                        "exit_code": result.returncode,
                        "finished_at": self._now_shanghai_iso(),
                        "logs": logs,
                        "error": {
                            "code": "build_failed",
                            "message": "构建命令执行失败。",
                        },
                    }
                )
        except subprocess.TimeoutExpired as exc:
            task = task.model_copy(
                update={
                    "status": "failed",
                    "finished_at": self._now_shanghai_iso(),
                    "logs": self._join_logs(exc.stdout, exc.stderr),
                    "error": {
                        "code": "build_timeout",
                        "message": f"构建超过 {self.build_timeout_seconds} 秒未完成。",
                    },
                }
            )
        except OSError as exc:
            task = task.model_copy(
                update={
                    "status": "failed",
                    "finished_at": self._now_shanghai_iso(),
                    "error": {
                        "code": "build_start_failed",
                        "message": str(exc),
                    },
                }
            )
        finally:
            self._tasks[task_id] = task
            self._lock.release()

        return task

    def get_task(self, task_id: str) -> TaskDTO:
        """读取构建任务状态。"""
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError("构建任务不存在。", code="task_not_found")
        return task

    def _clean_build_dir(self) -> None:
        """删除 site/build，路径必须确认位于 site 内。"""
        build_dir = settings.site_dir / "build"
        try:
            safe_build_dir = ensure_child_path(settings.site_dir, build_dir)
        except PathSecurityError as exc:
            raise AppError(
                "构建目录路径越界，已拒绝清理。",
                code="build_start_failed",
                status_code=500,
            ) from exc

        if safe_build_dir.exists():
            shutil.rmtree(safe_build_dir)

    @staticmethod
    def _build_command() -> list[str]:
        """返回平台兼容的 npm build 命令。"""
        if os.name == "nt":
            return ["cmd", "/c", "npm", "run", "build"]
        return ["npm", "run", "build"]

    @staticmethod
    def _join_logs(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
        """合并标准输出与错误输出。"""
        parts = []
        for value in (stdout, stderr):
            if isinstance(value, bytes):
                parts.append(value.decode("utf-8", errors="replace"))
            elif value:
                parts.append(value)
        return "\n".join(part.rstrip() for part in parts if part).strip()

    @staticmethod
    def _new_task_id() -> str:
        """生成构建任务 ID。"""
        return f"build-{datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S-%f')}"

    @staticmethod
    def _now_shanghai_iso() -> str:
        """返回当前上海时区 ISO 时间。"""
        return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
