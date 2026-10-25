from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_tag_service
from scr.main import app
from scr.schemas.tag import TagCreateDTO, TagDTO, TagSyncResultDTO


class FakeTagService:
    def __init__(self) -> None:
        self.list_tags_kwargs: dict[str, object] | None = None
        self.create_payload: TagCreateDTO | None = None
        self.sync_tags_kwargs: dict[str, object] | None = None

    def list_tags(self, **kwargs: object) -> list[TagDTO]:
        self.list_tags_kwargs = kwargs
        return [TagDTO(slug="python", label="Python", usage_count=3)]

    def create_tag(self, payload: TagCreateDTO) -> TagDTO:
        self.create_payload = payload
        return TagDTO(slug=payload.slug or "python", label=payload.label, description=payload.description)

    def sync_tags(self, **kwargs: object) -> TagSyncResultDTO:
        self.sync_tags_kwargs = kwargs
        return TagSyncResultDTO(
            dry_run=bool(kwargs["dry_run"]),
            requires_confirmation=not bool(kwargs["confirm"]),
            discovered_count=1,
            existing_count=2,
            created_tags=[],
            warnings=[],
        )


def test_list_tags_api_passes_filters_to_tag_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeTagService()
    app.dependency_overrides[get_tag_service] = lambda: fake_service

    response = client.get(
        "/api/v1/tags",
        params={
            "keyword": "py",
            "page": "2",
            "page_size": "10",
            "sort": "-usage",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "python"
    assert fake_service.list_tags_kwargs == {
        "keyword": "py",
        "page": 2,
        "page_size": 10,
        "sort": "-usage",
    }


def test_create_tag_api_uses_tag_service_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeTagService()
    app.dependency_overrides[get_tag_service] = lambda: fake_service

    response = client.post(
        "/api/v1/tags",
        json={
            "label": "Python",
            "slug": "python",
            "description": "Python notes",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "python"
    assert fake_service.create_payload is not None
    assert fake_service.create_payload.label == "Python"


def test_sync_tags_api_passes_confirmation_flags_to_tag_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeTagService()
    app.dependency_overrides[get_tag_service] = lambda: fake_service

    response = client.post(
        "/api/v1/tags/sync",
        params={
            "dry_run": "false",
            "confirm": "true",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["dry_run"] is False
    assert fake_service.sync_tags_kwargs == {"dry_run": False, "confirm": True}
