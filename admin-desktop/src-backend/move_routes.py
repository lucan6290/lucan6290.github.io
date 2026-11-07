from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from content_moves import ContentMoves


class MoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    destination: str
    kind: Literal["document", "directory"]


class ApplyRequest(MoveRequest):
    plan_id: str


def create_move_router(store):
    service = ContentMoves(store)
    router = APIRouter(prefix="/api/v1")

    @router.post("/moves/plan")
    def plan(payload: MoveRequest):
        return service.plan(payload.source, payload.destination, payload.kind)

    @router.post("/moves")
    def apply(payload: ApplyRequest):
        return service.apply(payload.source, payload.destination, payload.kind, payload.plan_id)

    @router.get("/links")
    def links():
        return service.graph()

    return router
