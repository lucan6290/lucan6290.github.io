"""轻量管理员鉴权。

仅支持单管理员账号，账号、密码与 token 密钥由环境变量提供。
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from scr.core.config import settings


PUBLIC_API_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/login",
}


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(payload: str) -> str:
    digest = hmac.new(settings.auth_secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def create_access_token(username: str) -> tuple[str, int]:
    """创建带过期时间的 HMAC token。"""
    now = int(time.time())
    expires_at = now + settings.auth_token_ttl_minutes * 60
    payload = {
        "sub": username,
        "iat": now,
        "exp": expires_at,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}", expires_at


def verify_access_token(token: str) -> dict[str, Any] | None:
    """校验 token 签名与过期时间，失败返回 None。"""
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError:
        return None

    if not hmac.compare_digest(signature, _sign(encoded_payload)):
        return None

    try:
        payload = json.loads(_base64url_decode(encoded_payload))
    except (json.JSONDecodeError, ValueError):
        return None

    username = payload.get("sub")
    expires_at = payload.get("exp")
    if username != settings.admin_username or not isinstance(expires_at, int):
        return None
    if expires_at <= int(time.time()):
        return None
    return payload


def authenticate_admin(username: str, password: str) -> bool:
    """常量时间比较管理员账号密码。"""
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password,
        settings.admin_password,
    )


def _extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    # 浏览器加载 <img>/<video> 等元素时无法附加 Authorization 头，
    # 允许通过 access_token query 参数传递会话 token 作为备选。
    # 日志中间件只记录 path 不记录 query，token 不会写入访问日志。
    query_token = request.query_params.get("access_token")
    if query_token and query_token.strip():
        return query_token.strip()
    return None


def _auth_error(message: str, code: str = "unauthorized", request_id: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNAUTHORIZED,
        content={
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": {},
        },
    )


async def admin_auth_middleware(request: Request, call_next):
    """保护 /api/v1 下除公开接口外的管理 API。"""
    path = request.url.path.rstrip("/") or "/"
    if request.method == "OPTIONS" or not path.startswith("/api/v1") or path in PUBLIC_API_PATHS:
        return await call_next(request)

    token = _extract_bearer_token(request)
    request_id = getattr(request.state, "request_id", None)
    if not token:
        return _auth_error("请先登录管理员后台。", request_id=request_id)

    payload = verify_access_token(token)
    if not payload:
        return _auth_error("登录状态已失效，请重新登录。", code="invalid_token", request_id=request_id)

    request.state.auth_user = payload["sub"]
    request.state.auth_expires_at = payload["exp"]
    return await call_next(request)
