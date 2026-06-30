"""HTTP 请求上下文中间件。

为每个请求注入唯一 request_id（贯穿日志与错误响应），
并在请求结束时记录方法、路径、状态码与耗时。
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response


logger = logging.getLogger(__name__)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """注入 request_id 并记录请求耗时。

    优先沿用客户端传入的 X-Request-ID，缺省则生成随机 hex，
    便于跨服务/前后端链路追踪。
    """
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id  # 供异常处理器与业务逻辑读取
    started_at = time.perf_counter()

    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id  # 回写到响应头，便于前端关联

    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response
