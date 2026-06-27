from __future__ import annotations

from pydantic import BaseModel


class UploadImageRequest(BaseModel):
    articlePath: str
    imageData: str
    extension: str


class AssetUsageRequest(BaseModel):
    articlePath: str
    content: str | None = None


class ImageInfo(BaseModel):
    name: str
    path: str
    url: str

