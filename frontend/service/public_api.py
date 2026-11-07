"""Optional HTTP API used by the static site's article tools."""

from dataclasses import dataclass, field
import hmac
import json
import os
from pathlib import Path
import re
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints, UUID4, field_validator
from starlette.datastructures import Headers, MutableHeaders

from author_routes import ContentError, attach_author_routes
from interaction_store import InteractionStore


BASE = "/api/v1"
MAX_ID = 2**63 - 1
RelativePath = Annotated[str, StringConstraints(min_length=1, max_length=1024)]
Before = Annotated[int | None, Query(ge=1, le=MAX_ID)]
CommentStatus = Literal["pending", "published", "rejected"]
ARTICLE_FILE = re.compile(r"\.(?:md|mdx)$", re.IGNORECASE)
RESOURCE_DIRECTORY = re.compile(r"^(?:images|assets|.*-imgs)$", re.IGNORECASE)


@dataclass(frozen=True)
class Settings:
    origin: str
    manifest: Path
    database: Path
    admin_token: str = field(default="", repr=False)
    author_project_root: Path | None = None

    def __post_init__(self):
        parsed = urlsplit(self.origin)
        host = parsed.hostname
        local = parsed.scheme == "http" and host in {"localhost", "127.0.0.1", "::1"}
        if (not host or self.origin != f"{parsed.scheme}://{parsed.netloc}" or parsed.username is not None
                or "*" in host or any(character.isspace() for character in host)
                or not (parsed.scheme == "https" or local)):
            raise ValueError("PUBLIC_SITE_ORIGIN 必须为 HTTPS 站点源，或本地 HTTP 站点源")
        if self.admin_token and not re.fullmatch(r"[!-~]{32,512}", self.admin_token):
            raise ValueError("管理员密钥必须为 32–512 个可打印 ASCII 字符")
        if self.author_project_root is not None and not self.admin_token:
            raise ValueError("启用在线写作时必须配置管理员密钥")

    @classmethod
    def from_env(cls):
        author_root = os.environ.get("PUBLIC_AUTHOR_PROJECT_ROOT")
        return cls(
            origin=os.environ["PUBLIC_SITE_ORIGIN"],
            manifest=Path(os.environ["PUBLIC_CONTENT_MANIFEST"]),
            database=Path(os.environ["PUBLIC_INTERACTION_DB"]),
            admin_token=os.environ.get("PUBLIC_ADMIN_TOKEN", ""),
            author_project_root=Path(author_root) if author_root else None,
        )


def published_paths(manifest):
    articles = json.loads(manifest.read_text(encoding="utf-8"))["articles"]
    paths = set()
    for route, article in articles.items():
        source = article["relativePath"]
        parts = source.split("/")
        if (len(source) > 1024 or "\\" in source or any(not part or part.startswith((".", "_")) for part in parts)
                or any(RESOURCE_DIRECTORY.fullmatch(part) for part in parts[:-1])
                or parts[-1].lower() == "readme.md" or not ARTICLE_FILE.search(source)
                or route != "/" + ARTICLE_FILE.sub("", source)):
            raise ValueError("公开文章清单包含无效路径")
        if len(parts) > 1:
            paths.add(source)
    return frozenset(paths)


def error_response(status, code, message):
    return JSONResponse(status_code=status, content={"code": code, "message": message},
                        headers={"WWW-Authenticate": "Bearer"} if status == 401 else None)


class ServiceError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


class RequestLimits:
    def __init__(self, app, *, origin):
        self.app = app
        self.origin = origin

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_no_store(message):
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-store"
            await send(message)

        headers = Headers(scope=scope)
        if headers.get("origin", self.origin) != self.origin:
            response = error_response(403, "origin_forbidden", "此站点源无权访问互动服务")
            return await response(scope, receive, send_no_store)

        if scope["method"] in {"POST", "PUT", "PATCH"}:
            path = scope["path"]
            root_path = scope.get("root_path", "")
            if root_path and path.startswith(root_path + "/"):
                path = path[len(root_path):]
            limit = 2 * 1024 * 1024 if path.startswith(f"{BASE}/admin/") else 32 * 1024
            declared = headers.get("content-length", "0")
            if not declared.isascii() or not declared.isdecimal() or len(declared) > 10 or int(declared) > limit:
                response = error_response(413, "body_too_large", "请求内容过长")
                return await response(scope, receive, send_no_store)
            if headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                response = error_response(415, "json_required", "请求必须使用 JSON")
                return await response(scope, receive, send_no_store)
            data = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(data) + len(chunk) > limit:
                    response = error_response(413, "body_too_large", "请求内容过长")
                    return await response(scope, receive, send_no_store)
                data.extend(chunk)
                if not message.get("more_body"):
                    break

            async def receive_body():
                return {"type": "http.request", "body": bytes(data), "more_body": False}

            receive = receive_body
        await self.app(scope, receive, send_no_store)


class ArticleRequest(BaseModel):
    article_path: RelativePath


class ViewRequest(ArticleRequest):
    session_id: UUID4


class CommentRequest(ArticleRequest):
    submission_id: UUID4
    body: str

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value):
        body = value.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not 1 <= len(body) <= 2000 or re.search(r"[\x00-\x08\x0b-\x1f\x7f\ud800-\udfff]", body):
            raise ValueError("评论需要 1–2000 个字符")
        return body


class ModerationRequest(BaseModel):
    status: Literal["published", "rejected"]


def create_app(settings=None):
    settings = settings or Settings.from_env()
    articles = published_paths(settings.manifest)
    store = InteractionStore(settings.database)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.add_middleware(RequestLimits, origin=settings.origin)
    app.add_middleware(CORSMiddleware, allow_origins=[settings.origin], allow_methods=["GET", "POST", "PUT", "PATCH"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(ServiceError)
    @app.exception_handler(ContentError)
    async def service_error(_request, error):
        return error_response(error.status, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error):
        return error_response(422, "invalid_request", "请求字段无效，请检查填写内容")

    def require_article(article_path):
        if article_path not in articles:
            raise ServiceError(404, "article_not_found", "互动服务未收录此文章")

    def require_limit(request, action, limit, seconds):
        client = request.client.host if request.client else "unknown"
        if not store.allow(action, client, limit, seconds):
            raise ServiceError(429, "rate_limit", "操作过于频繁，请稍后再试")

    def require_admin(request: Request, authorization: Annotated[str | None, Header()] = None):
        if not settings.admin_token:
            raise ServiceError(503, "admin_disabled", "站点尚未启用管理员服务")
        scheme, _, candidate = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(candidate.encode(), settings.admin_token.encode()):
            require_limit(request, "auth", 10, 60)
            raise ServiceError(401, "unauthorized", "管理员访问令牌无效")

    public = APIRouter(prefix=BASE)
    admin = APIRouter(prefix=f"{BASE}/admin", dependencies=[Depends(require_admin)])

    @public.get("/article")
    def article(article_path: RelativePath, before: Before = None):
        require_article(article_path)
        return {"views": store.count(article_path), **store.comments("published", before, article_path=article_path)}

    @public.post("/views")
    def views(payload: ViewRequest, request: Request):
        require_article(payload.article_path)
        require_limit(request, "view", 120, 60)
        return {"views": store.record_view(payload.article_path, payload.session_id)}

    @public.post("/comments", status_code=201)
    def submit(payload: CommentRequest, request: Request):
        require_article(payload.article_path)
        require_limit(request, "comment", 5, 600)
        if not store.submit(payload.article_path, payload.submission_id, payload.body):
            raise ServiceError(409, "submission_conflict", "此留言标识已经用于其他正文")
        return {"status": "accepted"}

    @admin.get("/comments")
    def comments(status: CommentStatus = "pending", before: Before = None):
        return store.comments(status, before)

    @admin.patch("/comments/{comment_id}")
    def moderate(comment_id: int, payload: ModerationRequest):
        result = store.moderate(comment_id, payload.status) if 1 <= comment_id <= MAX_ID else None
        if result is None:
            raise ServiceError(404, "comment_not_found", "评论不存在")
        return result

    attach_author_routes(admin, settings.author_project_root)
    app.include_router(public)
    app.include_router(admin)
    return app
