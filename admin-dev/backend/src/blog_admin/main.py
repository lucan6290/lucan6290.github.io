from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.admin.v1.router import router as admin_v1_router
from .core.errors import AppError
from .core.response import fail
from .core.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("blog-admin")


def create_app() -> FastAPI:
    app = FastAPI(
        title="箓川码笺管理后台 API",
        description="破坏式重构后的管理后台后端，模块化单体 + /api/admin/v1",
        version="2.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(admin_v1_router)
    return app


app = create_app()


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=fail(exc.code, exc.message, details=exc.details))


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else "请求失败"
    details = None if isinstance(detail, str) else detail
    return JSONResponse(status_code=exc.status_code, content=fail("HTTP_ERROR", message, details=details))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=fail("VALIDATION_ERROR", "请求参数校验失败", details={"errors": exc.errors()}),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("未处理异常: %s %s -> %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(status_code=500, content=fail("INTERNAL_ERROR", f"服务器内部错误: {exc}"))
