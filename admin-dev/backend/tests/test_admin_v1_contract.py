"""Contract tests for the backend v1 admin API.

These tests intentionally avoid write-heavy routes, Git commands, and AI
network calls. They codify the expected public surface for the breaking
backend refactor and should pass once the new /api/admin/v1 namespace exists.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

APP_IMPORT_CANDIDATES = (
    "blog_admin.main:app",
    "src.blog_admin.main:app",
)

EXPECTED_ROUTE_METHODS: dict[str, set[str]] = {
    "/api/admin/v1/health": {"GET"},
    "/api/admin/v1/posts": {"GET", "POST"},
    "/api/admin/v1/posts/{path}": {"GET", "PUT", "DELETE"},
    "/api/admin/v1/categories/registry": {"GET", "PUT"},
    "/api/admin/v1/articles/index": {"GET"},
    "/api/admin/v1/articles/index/scan": {"POST"},
    "/api/admin/v1/articles/knowledge-qa": {"POST"},
    "/api/admin/v1/assets/images": {"POST"},
    "/api/admin/v1/assets/images/{article_path}": {"GET"},
    "/api/admin/v1/assets/images/{path}": {"DELETE"},
    "/api/admin/v1/assets/folders": {"GET", "POST"},
    "/api/admin/v1/assets/file/{path}": {"GET"},
    "/api/admin/v1/ai/presets": {"GET"},
    "/api/admin/v1/ai/test": {"POST"},
    "/api/admin/v1/ai/chat": {"POST"},
    "/api/admin/v1/git/commit": {"POST"},
    "/api/admin/v1/git/push": {"POST"},
    "/api/admin/v1/git/deploy": {"POST"},
}


def _load_app() -> FastAPI:
    errors: list[str] = []
    for candidate in APP_IMPORT_CANDIDATES:
        module_name, app_name = candidate.split(":", 1)
        try:
            module = import_module(module_name)
            app = getattr(module, app_name)
        except Exception as exc:  # pragma: no cover - only used for diagnostics
            errors.append(f"{candidate}: {exc!r}")
            continue
        if isinstance(app, FastAPI):
            return app
        errors.append(f"{candidate}: exported object is not a FastAPI app")

    pytest.fail("Unable to import backend FastAPI app. Tried:\n" + "\n".join(errors))


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return _load_app()


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.mark.contract
def test_admin_v1_health_contract(client: TestClient) -> None:
    response = client.get("/api/admin/v1/health")

    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload.get("success") is True
    assert isinstance(payload.get("data"), dict)
    assert payload["data"].get("status") in {"ok", "healthy"}


def _assert_success_envelope(payload: dict[str, Any]) -> None:
    assert payload.get("success") is True
    assert "data" in payload
    assert "error" not in payload


def _assert_error_envelope(payload: dict[str, Any], *, code: str | None = None) -> None:
    assert payload.get("success") is False
    error = payload.get("error")
    assert isinstance(error, dict)
    assert isinstance(error.get("code"), str)
    assert isinstance(error.get("message"), str)
    if code is not None:
        assert error.get("code") == code


@pytest.mark.contract
def test_admin_v1_categories_success_envelope(client: TestClient) -> None:
    response = client.get("/api/admin/v1/categories/registry")

    assert response.status_code == 200
    _assert_success_envelope(response.json())


@pytest.mark.contract
def test_admin_v1_categories_error_envelope(client: TestClient) -> None:
    response = client.put("/api/admin/v1/categories/registry", json=[{}])

    assert response.status_code == 200
    _assert_error_envelope(response.json(), code="CATEGORY_REGISTRY_INVALID")


@pytest.mark.contract
def test_admin_v1_posts_not_found_error_envelope(client: TestClient) -> None:
    response = client.get("/api/admin/v1/posts/not-found.md")

    assert response.status_code == 200
    _assert_error_envelope(response.json(), code="POST_NOT_FOUND")


@pytest.mark.contract
def test_admin_v1_create_post_invalid_category_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/admin/v1/posts",
        json={"title": "契约测试文章", "prefix1": "unknown", "prefix2": "demo"},
    )

    assert response.status_code == 200
    _assert_error_envelope(response.json(), code="POST_CATEGORY_INVALID")


@pytest.mark.contract
def test_admin_v1_assets_business_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/admin/v1/assets/images",
        json={"articlePath": "", "imageData": "", "extension": ""},
    )

    assert response.status_code == 200
    _assert_error_envelope(response.json(), code="VALIDATION_ERROR")


@pytest.mark.contract
def test_admin_v1_validation_error_envelope(client: TestClient) -> None:
    response = client.post("/api/admin/v1/assets/images", json={})

    assert response.status_code == 422
    _assert_error_envelope(response.json(), code="VALIDATION_ERROR")


@pytest.mark.contract
def test_admin_v1_route_surface_exists(app: FastAPI) -> None:
    openapi = app.openapi()
    paths: dict[str, dict[str, Any]] = openapi["paths"]

    missing_paths = sorted(set(EXPECTED_ROUTE_METHODS) - set(paths))
    assert not missing_paths, f"Missing admin v1 paths: {missing_paths}"

    missing_methods: dict[str, list[str]] = {}
    for path, expected_methods in EXPECTED_ROUTE_METHODS.items():
        actual_methods = {method.upper() for method in paths[path] if method != "parameters"}
        missing = sorted(expected_methods - actual_methods)
        if missing:
            missing_methods[path] = missing

    assert not missing_methods, f"Missing admin v1 methods: {missing_methods}"


@pytest.mark.contract
def test_compat_api_is_not_the_only_registered_surface(app: FastAPI) -> None:
    paths = set(app.openapi()["paths"])

    assert "/api/admin/v1/health" in paths
    assert any(path.startswith("/api/admin/v1/") for path in paths)

