from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_blog_index_service, get_category_index_service, get_sidebar_management_service
from scr.main import app
from scr.schemas.common import MutationPlanDTO
from scr.schemas.sidebar import SidebarStatusDTO, SidebarSyncDTO


def _mutation_plan(dry_run: bool) -> MutationPlanDTO:
    return MutationPlanDTO(dry_run=dry_run, requires_confirmation=dry_run, changes=[], warnings=[])


class FakeSidebarManagementService:
    def __init__(self) -> None:
        self.status_kwargs: dict[str, object] | None = None
        self.sync_payload: SidebarSyncDTO | None = None

    def get_status(self, **kwargs: object) -> SidebarStatusDTO:
        self.status_kwargs = kwargs
        return SidebarStatusDTO(
            type="blog",
            sidebars_exists=True,
            sidebars_path="site/blogSidebars.ts",
            docs_count=2,
            registered_count=1,
            missing_count=1,
            orphan_count=0,
            registered_doc_ids=[],
            missing_in_sidebars=[],
            orphan_sidebar_ids=[],
            blog_category_count=1,
        )

    def sync(self, payload: SidebarSyncDTO) -> MutationPlanDTO:
        self.sync_payload = payload
        return _mutation_plan(payload.dry_run)


class FakeIndexSyncService:
    def __init__(self) -> None:
        self.sync_all_kwargs: dict[str, object] | None = None

    def sync_all(self, **kwargs: object) -> MutationPlanDTO:
        self.sync_all_kwargs = kwargs
        return _mutation_plan(bool(kwargs["dry_run"]))


def test_sidebar_status_api_passes_query_to_sidebar_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeSidebarManagementService()
    app.dependency_overrides[get_sidebar_management_service] = lambda: fake_service

    response = client.get(
        "/api/v1/sidebars/status",
        params={
            "include_details": "false",
            "type": "blog",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["type"] == "blog"
    assert fake_service.status_kwargs == {"include_details": False, "type": "blog"}


def test_sidebar_sync_api_uses_sidebar_service_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeSidebarManagementService()
    app.dependency_overrides[get_sidebar_management_service] = lambda: fake_service

    response = client.post(
        "/api/v1/sidebars/sync",
        json={
            "type": "blog",
            "mode": "sync_categories",
            "dry_run": False,
            "confirm": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["dry_run"] is False
    assert fake_service.sync_payload is not None
    assert fake_service.sync_payload.mode == "sync_categories"


def test_docs_index_sync_api_passes_flags_to_category_index_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeIndexSyncService()
    app.dependency_overrides[get_category_index_service] = lambda: fake_service

    response = client.post(
        "/api/v1/sidebars/docs-index/sync",
        json={
            "dry_run": False,
            "confirm": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert fake_service.sync_all_kwargs == {"dry_run": False, "confirm": True}


def test_blog_index_sync_api_passes_flags_to_blog_index_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeIndexSyncService()
    app.dependency_overrides[get_blog_index_service] = lambda: fake_service

    response = client.post(
        "/api/v1/sidebars/blog-index/sync",
        json={
            "dry_run": True,
            "confirm": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert fake_service.sync_all_kwargs == {"dry_run": True, "confirm": False}
