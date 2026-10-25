"""GitHub 同步与 SSH Deploy Key 端点。"""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_git_sync_service
from scr.schemas.git_sync import (
    GitCommandResultDTO,
    GitPullRequestDTO,
    GitRemoteUpdateDTO,
    GitSshKeyCreateDTO,
    GitSyncStatusDTO,
)
from scr.services.site.git_sync_service import GitSyncService


router = APIRouter(prefix="/git-sync", tags=["git-sync"])


@router.get("/status", response_model=GitSyncStatusDTO)
def get_git_sync_status(
    git_sync_service: GitSyncService = Depends(get_git_sync_service),
) -> GitSyncStatusDTO:
    """读取当前 Git/GitHub 配置状态。"""
    return git_sync_service.get_status()


@router.post("/ssh-key", response_model=GitCommandResultDTO)
def create_ssh_key(
    payload: GitSshKeyCreateDTO,
    git_sync_service: GitSyncService = Depends(get_git_sync_service),
) -> GitCommandResultDTO:
    """生成服务器 SSH Deploy Key。"""
    return git_sync_service.create_ssh_key(payload)


@router.post("/remote", response_model=GitCommandResultDTO)
def update_remote(
    payload: GitRemoteUpdateDTO,
    git_sync_service: GitSyncService = Depends(get_git_sync_service),
) -> GitCommandResultDTO:
    """更新 origin 远端地址。"""
    return git_sync_service.update_remote(payload)


@router.post("/ssh-test", response_model=GitCommandResultDTO)
def test_ssh(
    git_sync_service: GitSyncService = Depends(get_git_sync_service),
) -> GitCommandResultDTO:
    """测试 GitHub SSH 连接。"""
    return git_sync_service.test_ssh()


@router.post("/pull", response_model=GitCommandResultDTO)
def pull_from_github(
    payload: GitPullRequestDTO,
    git_sync_service: GitSyncService = Depends(get_git_sync_service),
) -> GitCommandResultDTO:
    """从 GitHub 拉取最新代码和文章到服务器。"""
    return git_sync_service.pull(payload)
