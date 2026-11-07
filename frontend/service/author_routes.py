"""Authenticated Markdown endpoints backed by the desktop content store."""

from pathlib import Path
import sys
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, StringConstraints


DESKTOP_BACKEND = Path(__file__).resolve().parents[2] / "admin-desktop" / "src-backend"
sys.path.insert(0, str(DESKTOP_BACKEND))
from content_mutations import mutable_path
from content_store import ContentError, ContentStore, RESOURCE_DIRECTORY


AuthorPath = Annotated[str, StringConstraints(min_length=1, max_length=1024)]
RawMarkdown = Annotated[str, StringConstraints(max_length=500_000)]
Version = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class DocumentRequest(BaseModel):
    relative_path: AuthorPath
    raw_content: RawMarkdown


class SaveRequest(DocumentRequest):
    expected_version: Version | None = None


def document_summary(data):
    return {field: data[field] for field in ("relative_path", "title")}


def document_detail(data):
    return {**document_summary(data), "raw_content": data["raw_content"], "version": data["version"]}


def validate_path(content, relative_path):
    target = mutable_path(content, relative_path)
    if any(RESOURCE_DIRECTORY.fullmatch(part) for part in target.relative_to(content.content_root).parts[:-1]):
        raise ContentError(400, "invalid_path", "写作只支持内容分类中的 Markdown")


def attach_author_routes(admin: APIRouter, project_root: Path | None):
    content = ContentStore(project_root) if project_root is not None else None

    def require_writer():
        if content is None:
            raise ContentError(503, "writing_disabled", "站点尚未启用在线写作")
        return content

    @admin.get("/session")
    def session():
        return {"writing_enabled": content is not None}

    @admin.get("/documents")
    def documents():
        store = require_writer()
        with store.lock:
            listing = store.list_content()
        return {
            "documents": [document_summary(document) for document in listing["documents"]],
            "directories": [
                {field: directory[field] for field in ("relative_path", "label")}
                for directory in listing["directories"]
            ],
        }

    @admin.get("/document")
    def open_document(relative_path: AuthorPath):
        store = require_writer()
        with store.lock:
            validate_path(store, relative_path)
            return document_detail(store.detail(relative_path))

    @admin.post("/documents", status_code=201)
    def create_document(payload: DocumentRequest):
        store = require_writer()
        with store.lock:
            validate_path(store, payload.relative_path)
            return document_detail(store.create(payload.relative_path, payload.raw_content))

    @admin.put("/document")
    def save_document(payload: SaveRequest):
        store = require_writer()
        with store.lock:
            validate_path(store, payload.relative_path)
            return document_detail(store.save(payload.relative_path, payload.raw_content, payload.expected_version))
