"""构建端点。"""

from fastapi import APIRouter

from scr.schemas.build import BuildRequestDTO, TaskDTO
from scr.services.site.build_service import BuildService


router = APIRouter(prefix="/build", tags=["build"])
build_service = BuildService()


@router.post("", response_model=TaskDTO)
def run_build(payload: BuildRequestDTO = BuildRequestDTO()) -> TaskDTO:
    """执行站点构建验证。"""
    return build_service.run_build(payload)


@router.get("/tasks/{task_id}", response_model=TaskDTO)
def get_build_task(task_id: str) -> TaskDTO:
    """获取构建任务状态和日志。"""
    return build_service.get_task(task_id)
