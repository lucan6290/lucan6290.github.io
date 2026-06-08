"""
博客管理后台 - FastAPI 主应用
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, SERVER_PORT
from .routers import ai, assets, files, git_config, git_ops
from .schemas import ApiResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("blog-admin")

# ============================================================
# 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="博客管理后台 API",
    description="箓川码笺（lucan6290.github.io）管理后台后端，Python FastAPI + LangChain",
    version="1.0.0",
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 注册路由
# ============================================================

app.include_router(files.router)
app.include_router(assets.router)
app.include_router(git_ops.router)
app.include_router(git_config.router)
app.include_router(ai.router)


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health():
    return ApiResponse(success=True, data={"status": "ok"})


@app.get("/api/health")
async def api_health():
    """供前端路由守卫使用"""
    return ApiResponse(success=True, data={"status": "ok"})


# ============================================================
# 全局异常处理
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("未处理异常: %s %s → %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ApiResponse(success=False, error=f"服务器内部错误: {exc}").model_dump(),
    )
