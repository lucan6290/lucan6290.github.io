"""全局异常处理器注册。

将三类异常统一转换为结构化错误响应，格式与 ErrorResponseDTO 对齐：
code / message / request_id / details，保证前端可用稳定契约处理错误。
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from scr.core.exceptions import AppError


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """向 app 注册全部异常处理器。"""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        """处理业务异常：按 exc 携带的 status_code 与 code 返回。"""
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "Handled application error",
            extra={
                "request_id": request_id,
                "error_code": exc.code,
                "path": request.url.path,
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "details": jsonable_encoder(exc.details),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """处理请求参数校验失败（如查询参数类型不符），统一返回 422。"""
        request_id = getattr(request.state, "request_id", None)
        logger.info(
            "Request validation failed",
            extra={"request_id": request_id, "path": request.url.path},
        )
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content={
                "code": "request_validation_error",
                "message": "请求参数校验失败。",
                "request_id": request_id,
                "details": {"errors": jsonable_encoder(exc.errors())},
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """兜底处理未捕获异常：记录完整堆栈，对外返回 500 与通用文案，避免泄露内部细节。"""
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled application error",
            extra={"request_id": request_id, "path": request.url.path},
        )
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "code": "internal_error",
                "message": "服务暂时不可用。",
                "request_id": request_id,
                "details": {},
            },
        )
