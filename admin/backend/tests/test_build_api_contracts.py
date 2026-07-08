from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_build_service
from scr.main import app
from scr.schemas.build import BuildRequestDTO, TaskDTO


class FakeBuildService:
    def __init__(self) -> None:
        self.run_payload: BuildRequestDTO | None = None
        self.task_id: str | None = None

    def run_build(self, payload: BuildRequestDTO) -> TaskDTO:
        self.run_payload = payload
        return TaskDTO(
            task_id="build-test",
            type="build",
            status="success",
            started_at="2026-07-03T00:00:00+08:00",
            finished_at="2026-07-03T00:00:01+08:00",
            exit_code=0,
            logs="ok",
        )

    def get_task(self, task_id: str) -> TaskDTO:
        self.task_id = task_id
        return TaskDTO(
            task_id=task_id,
            type="build",
            status="running",
            started_at="2026-07-03T00:00:00+08:00",
        )


def test_run_build_api_passes_payload_to_build_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeBuildService()
    app.dependency_overrides[get_build_service] = lambda: fake_service

    response = client.post(
        "/api/v1/build",
        json={
            "command": "build",
            "clean": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["task_id"] == "build-test"
    assert fake_service.run_payload is not None
    assert fake_service.run_payload.clean is True


def test_get_build_task_api_uses_build_service_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeBuildService()
    app.dependency_overrides[get_build_service] = lambda: fake_service

    response = client.get("/api/v1/build/tasks/build-123", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["task_id"] == "build-123"
    assert fake_service.task_id == "build-123"
