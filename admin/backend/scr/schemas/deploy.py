"""发布相关 DTO。"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DeployRequestDTO(BaseModel):
    """执行发布请求 DTO。"""

    branch: str = Field(default="develop", min_length=1, max_length=120)
    commit_message: str = Field(min_length=1, max_length=200)
    run_build_first: bool = True
    clean_build: bool = False

    @field_validator("branch")
    @classmethod
    def normalize_branch(cls, value: str) -> str:
        branch = value.strip()
        if not branch:
            raise ValueError("目标分支不能为空。")
        return branch

    @field_validator("commit_message")
    @classmethod
    def normalize_commit_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("提交信息不能为空。")
        return message


class DeployResultDTO(BaseModel):
    """发布结果 DTO。"""

    status: Literal["success", "failed", "no_changes"]
    branch: str
    commit: str | None = None
    pushed: bool = False
    logs: str = ""
    error: dict[str, Any] | None = None
