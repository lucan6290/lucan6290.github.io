from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_deploy_service
from scr.main import app
from scr.schemas.deploy import DeployRequestDTO, DeployResultDTO


class FakeDeployService:
    def __init__(self) -> None:
        self.payload: DeployRequestDTO | None = None

    def run_deploy(self, payload: DeployRequestDTO) -> DeployResultDTO:
        self.payload = payload
        return DeployResultDTO(
            status="success",
            branch=payload.branch,
            commit="abc123",
            pushed=True,
            logs="$ git push origin HEAD:develop",
        )


def test_run_deploy_api_passes_payload_to_deploy_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeDeployService()
    app.dependency_overrides[get_deploy_service] = lambda: fake_service

    response = client.post(
        "/api/v1/deploy",
        json={
            "branch": "develop",
            "commit_message": "publish: test",
            "run_build_first": True,
            "clean_build": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["branch"] == "develop"
    assert fake_service.payload is not None
    assert fake_service.payload.commit_message == "publish: test"
