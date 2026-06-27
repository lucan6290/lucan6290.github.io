from __future__ import annotations

from fastapi import APIRouter

from blog_admin.modules.gitops.application import git_service
from blog_admin.modules.gitops.schemas import GitCommitRequest

router = APIRouter(prefix="/git", tags=["Git 操作"])


@router.post("/commit")
async def git_commit(req: GitCommitRequest):
    return await git_service.commit(req)


@router.post("/push")
async def git_push():
    return await git_service.push()


@router.post("/deploy")
async def git_deploy(req: GitCommitRequest):
    return await git_service.deploy(req)

