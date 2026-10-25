"""Git 同步相关 DTO。"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GitSyncStatusDTO(BaseModel):
    """当前仓库 Git/GitHub 连接状态。"""

    current_branch: str
    remote_url: str | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None
    ssh_key_path: str
    public_key: str | None = None
    has_private_key: bool = False
    remote_uses_ssh: bool = False
    is_dirty: bool = False
    changes: list[str] = Field(default_factory=list)


class GitRemoteUpdateDTO(BaseModel):
    """更新 origin 远端地址。"""

    remote_url: str = Field(min_length=1, max_length=500)

    @field_validator("remote_url")
    @classmethod
    def normalize_remote_url(cls, value: str) -> str:
        remote_url = value.strip()
        if not remote_url:
            raise ValueError("远端地址不能为空。")
        return remote_url


class GitSshKeyCreateDTO(BaseModel):
    """生成服务器 SSH Deploy Key。"""

    email: str | None = Field(default=None, max_length=200)
    overwrite: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        email = value.strip()
        return email or None


class GitPullRequestDTO(BaseModel):
    """从 GitHub 拉取并更新服务器工作区。"""

    branch: str = Field(default="develop", min_length=1, max_length=120)
    mode: Literal["ff_only", "rebase"] = "ff_only"
    run_build_after: bool = False

    @field_validator("branch")
    @classmethod
    def normalize_branch(cls, value: str) -> str:
        branch = value.strip()
        if not branch:
            raise ValueError("目标分支不能为空。")
        return branch


class GitCommandResultDTO(BaseModel):
    """Git 运维命令执行结果。"""

    status: Literal["success", "failed"]
    branch: str | None = None
    logs: str = ""
    error: dict[str, str] | None = None
