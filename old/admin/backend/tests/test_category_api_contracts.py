from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_category_service, get_category_workflow_service
from scr.main import app
from scr.models.article import ArticleType
from scr.schemas.category import CategoryCreateDTO, CategoryDTO


def _category() -> CategoryDTO:
    return CategoryDTO(
        id="docs:tech",
        type=ArticleType.docs,
        slug="tech",
        label="Tech",
        path=["tech"],
        description=None,
        cover=None,
        sort_order=1,
        enabled=True,
        article_count=0,
        children=[],
    )


class FakeCategoryService:
    def __init__(self) -> None:
        self.list_categories_kwargs: dict[str, object] | None = None

    def list_categories(self, **kwargs: object) -> list[CategoryDTO]:
        self.list_categories_kwargs = kwargs
        return [_category()]


class FakeCategoryWorkflow:
    def __init__(self) -> None:
        self.payload: CategoryCreateDTO | None = None

    def create_category(self, payload: CategoryCreateDTO) -> CategoryDTO:
        self.payload = payload
        return _category()


def test_list_categories_api_passes_filters_to_category_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeCategoryService()
    app.dependency_overrides[get_category_service] = lambda: fake_service
    response = client.get(
        "/api/v1/categories",
        params={
            "type": "docs",
            "include_empty": "false",
            "include_counts": "true",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == "docs:tech"
    assert fake_service.list_categories_kwargs == {
        "article_type": ArticleType.docs,
        "include_empty": False,
        "include_counts": True,
    }


def test_create_category_api_uses_category_workflow_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_workflow = FakeCategoryWorkflow()
    app.dependency_overrides[get_category_workflow_service] = lambda: fake_workflow
    response = client.post(
        "/api/v1/categories",
        json={
            "type": "docs",
            "path": ["tech"],
            "label": "Tech",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["id"] == "docs:tech"
    assert fake_workflow.payload is not None
    assert fake_workflow.payload.path == ["tech"]
    assert fake_workflow.payload.type == ArticleType.docs
