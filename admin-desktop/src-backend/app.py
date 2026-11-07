"""桌面内容 HTTP 契约，不导入旧管理工作流。"""
from pathlib import Path
import secrets

from fastapi import Depends, FastAPI, Header, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, StrictBool

from content_store import ContentError, ContentStore


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relative_path: str


class WritePayload(Payload):
    raw_content: str


class CreatePayload(WritePayload):
    article: StrictBool = True


class SavePayload(WritePayload):
    expected_version: str | None = None
    article: StrictBool | None = None


class DeletePayload(Payload):
    expected_version: str | None = None
    confirm: StrictBool = False


def create_app(project_root: Path, token: str):
    if not token:
        raise ValueError("会话 token 不能为空")
    store = ContentStore(project_root)
    app = FastAPI(title="箓川码笺桌面内容服务", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=[
        "http://tauri.localhost", "https://tauri.localhost", "tauri://localhost",
        "http://localhost:14200", "http://127.0.0.1:14200",
    ], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(ContentError)
    async def content_error(_request, error):
        body = {"code": error.code, "message": error.message}
        if error.details is not None:
            body["details"] = error.details
        return JSONResponse(status_code=error.status, content=jsonable_encoder(body))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, error):
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "请求字段无效", "details": jsonable_encoder(error.errors())})

    def authenticate(authorization: str | None = Header(default=None)):
        if not authorization or not secrets.compare_digest(authorization, f"Bearer {token}"):
            raise ContentError(401, "unauthorized", "会话认证失败")

    @app.get("/health")
    def health():
        return {"service": "xiaocancoding-content", "api_version": 1,
                "project_root": str(store.project_root), "content_root": str(store.content_root)}

    dependencies = [Depends(authenticate)]

    @app.get("/api/v1/content", dependencies=dependencies)
    def content(query: str = Query(default="", max_length=200)):
        return store.list_content(query)

    @app.get("/api/v1/images", dependencies=dependencies)
    def image(path: str):
        target, media_type = store.image(path)
        return FileResponse(target, media_type=media_type, headers={"X-Content-Type-Options": "nosniff"})

    @app.get("/api/v1/documents/version", dependencies=dependencies)
    def version(path: str):
        return store.version(path)

    @app.get("/api/v1/documents", dependencies=dependencies)
    def document(path: str):
        return store.detail(path)

    @app.post("/api/v1/documents", status_code=201, dependencies=dependencies)
    def create(payload: CreatePayload):
        return store.create(payload.relative_path, payload.raw_content, payload.article)

    @app.put("/api/v1/documents", dependencies=dependencies)
    def save(payload: SavePayload):
        return store.save(payload.relative_path, payload.raw_content, payload.expected_version, payload.article)

    @app.delete("/api/v1/documents", dependencies=dependencies)
    def delete(payload: DeletePayload):
        return store.delete(payload.relative_path, payload.expected_version, payload.confirm)

    @app.post("/api/v1/directories", status_code=201, dependencies=dependencies)
    def directory(payload: Payload):
        return store.create_directory(payload.relative_path)

    return app
