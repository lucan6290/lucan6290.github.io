from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, StrictBool

from media_library import MediaLibrary


class ImportImage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_path: str
    filename: str
    data_base64: str


class DeleteImage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relative_path: str
    plan_id: str
    confirm: StrictBool


def create_media_router(store):
    library = MediaLibrary(store)
    router = APIRouter(prefix="/api/v1/media")

    @router.get("")
    def list_images(document_path: str):
        return {"images": library.list_images(document_path)}

    @router.post("", status_code=201)
    def import_image(payload: ImportImage):
        return library.import_image(payload.document_path, payload.filename, payload.data_base64)

    @router.get("/delete-plan")
    def delete_plan(path: str):
        return library.delete_plan(path)

    @router.delete("")
    def delete_image(payload: DeleteImage):
        return library.delete(payload.relative_path, payload.plan_id, payload.confirm)

    return router
