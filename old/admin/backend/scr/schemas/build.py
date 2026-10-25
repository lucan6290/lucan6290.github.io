"""构建相关 DTO。"""

from typing import Any, Literal

from pydantic import BaseModel, field_validator


class BuildRequestDTO(BaseModel):
    """执行构建验证请求 DTO。"""

    command: Literal["build"] = "build"
    clean: bool = False

    @field_validator("command")
    @classmethod
    def validate_command(cls, value: str) -> str:
        if value != "build":
            raise ValueError("command 当前固定为 build。")
        return value


class TaskDTO(BaseModel):
    """任务响应 DTO。"""

    task_id: str
    type: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    logs: str = ""
    error: dict[str, Any] | None = None
