"""使用桌面会话认证的 Git 工作区 HTTP 适配器。"""
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from content_store import ContentError
from git_workspace import GitWorkspace


class PreviewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["commit", "update", "push", "publish"]
    paths: list[str] = Field(default_factory=list, max_length=1000)
    message: str | None = Field(default=None, max_length=100)


class ConfirmPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=100)
    confirm: StrictBool = False


def create_git_router(project_root: Path):
    router = APIRouter(prefix="/api/v1/git")
    workspace = GitWorkspace(project_root)

    @router.get("/status")
    def status():
        return workspace.status()

    @router.get("/diff")
    def diff(path: str = Query(max_length=4096)):
        return workspace.diff(path)

    @router.post("/preview")
    def preview(payload: PreviewPayload):
        return workspace.preview(payload.action, payload.paths, payload.message)

    @router.post("/execute")
    def execute(payload: ConfirmPayload):
        if payload.confirm is not True:
            raise ContentError(400, "git_confirmation_required", "请明确确认操作预览")
        return workspace.execute(payload.token)

    return router
