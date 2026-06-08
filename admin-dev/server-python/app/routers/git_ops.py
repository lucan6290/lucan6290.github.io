"""
Git 操作路由
POST /api/git/commit | push | deploy
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from ..config import BLOG_ROOT
from ..schemas import ApiResponse, GitCommitRequest

router = APIRouter(prefix="/api/git", tags=["Git 操作"])


async def _run_git(*args: str, cwd: str = str(BLOG_ROOT)) -> tuple[str, str]:
    """异步执行 git 命令"""
    cmd = ["git"] + list(args)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败 (code={proc.returncode}): "
            f"{stderr.decode('utf-8', errors='replace')}"
        )
    return stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")


# ============================================================
# 路由
# ============================================================

@router.post("/commit")
async def git_commit(req: GitCommitRequest):
    """执行 git add . && git commit"""
    if not req.message:
        return ApiResponse(success=False, error="提交信息不能为空")

    try:
        await _run_git("add", ".")
        stdout, stderr = await _run_git("commit", "-m", req.message)
        return ApiResponse(success=True, data={"stdout": stdout, "stderr": stderr})
    except RuntimeError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git commit 失败: {e}")


@router.post("/push")
async def git_push():
    """执行 git push origin"""
    try:
        stdout, stderr = await _run_git("push", "origin")
        return ApiResponse(success=True, data={"stdout": stdout, "stderr": stderr})
    except RuntimeError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git push 失败: {e}")


@router.post("/deploy")
async def git_deploy(req: GitCommitRequest):
    """一键部署：git add (指定文件或全部) && git commit && git push"""
    if not req.message:
        return ApiResponse(success=False, error="提交信息不能为空")

    try:
        # 如果指定了文件路径，只 add 该文件；否则 add 所有变更
        if req.filePath:
            await _run_git("add", req.filePath)
        else:
            await _run_git("add", ".")
        commit_out, commit_err = await _run_git("commit", "-m", req.message)
        push_out, push_err = await _run_git("push", "origin")

        return ApiResponse(success=True, data={
            "commit": {"stdout": commit_out, "stderr": commit_err},
            "push": {"stdout": push_out, "stderr": push_err},
        })
    except RuntimeError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git deploy 失败: {e}")
