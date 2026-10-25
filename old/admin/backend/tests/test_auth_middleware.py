from fastapi.testclient import TestClient

from scr.core.config import settings


def test_protected_api_unauthorized_response_includes_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/articles")

    assert response.status_code == 401
    request_id = response.headers["x-request-id"]
    assert request_id
    assert response.json()["request_id"] == request_id


def test_public_api_still_includes_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_login_token_allows_current_session_lookup(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    session_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert session_response.status_code == 200
    assert session_response.json()["authenticated"] is True
    assert session_response.json()["username"] == settings.admin_username


def test_invalid_login_uses_structured_error_response(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.admin_username,
            "password": "definitely-wrong",
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "invalid_credentials"
    assert body["request_id"] == response.headers["x-request-id"]
