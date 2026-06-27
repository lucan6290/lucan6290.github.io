from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from blog_admin.core.schemas import ChatRequest, TestConnectionRequest
from blog_admin.modules.ai import application
from blog_admin.modules.ai.schemas import AgentCommitRequest, AgentPlanRequest, EditApplyRequest, EditPlanRequest

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/presets")
async def get_presets():
    return await application.get_presets()


@router.post("/test")
async def test_connection(req: TestConnectionRequest):
    return await application.test_connection(req)


@router.post("/chat")
async def chat(req: ChatRequest):
    return await application.chat(req)


@router.post("/writing/material/extract")
async def extract_material(file: UploadFile = File(...)):
    return await application.extract_material(file)


@router.post("/writing/agent/plan")
async def agent_plan(req: AgentPlanRequest):
    return await application.agent_plan(req)


@router.post("/writing/agent/commit")
async def agent_commit(req: AgentCommitRequest):
    return await application.agent_commit(req)


@router.post("/writing/edit/plan")
async def edit_plan(req: EditPlanRequest):
    return await application.edit_plan(req)


@router.post("/writing/edit/apply")
async def edit_apply(req: EditApplyRequest):
    return await application.edit_apply(req)
