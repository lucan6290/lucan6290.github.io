from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from scr.core.config import settings
from scr.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
