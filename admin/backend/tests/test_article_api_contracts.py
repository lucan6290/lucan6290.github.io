from fastapi.testclient import TestClient

from scr.api.v1.dependencies import get_article_service, get_article_workflow_service
from scr.main import app
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO, ArticleListResponseDTO


def _article_detail() -> ArticleDetailDTO:
    return ArticleDetailDTO(
        id="docs:test.md",
        type=ArticleType.docs,
        type_label="docs",
        title="Test Article",
        description=None,
        date=None,
        last_update=None,
        relative_path="test.md",
        route="/docs/test",
        slug="test",
        tags=[],
        authors=[],
        category_path=[],
        category_label="docs",
        sidebar_registered=True,
        version="v1",
        updated_at="2026-07-03T00:00:00+08:00",
        issues=[],
        frontmatter={"title": "Test Article"},
        body="Body",
        raw_content="---\ntitle: Test Article\n---\nBody",
    )


class FakeArticleService:
    def __init__(self) -> None:
        self.list_articles_kwargs: dict[str, object] | None = None

    def list_articles(self, **kwargs: object) -> ArticleListResponseDTO:
        self.list_articles_kwargs = kwargs
        return ArticleListResponseDTO(
            items=[],
            page=int(kwargs["page"]),
            page_size=int(kwargs["page_size"]),
            total=0,
            has_next=False,
        )


class FakeArticleWorkflow:
    def __init__(self) -> None:
        self.payload: ArticleCreateDTO | None = None

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        self.payload = payload
        return _article_detail()


def test_list_articles_api_passes_filters_to_article_service(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_service = FakeArticleService()
    app.dependency_overrides[get_article_service] = lambda: fake_service
    response = client.get(
        "/api/v1/articles",
        params={
            "type": "blog",
            "keyword": "ai",
            "tag": "Python",
            "author": "lucan",
            "category": "tech",
            "has_issues": "true",
            "page": "2",
            "page_size": "5",
            "sort": "-date",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 2, "page_size": 5, "total": 0, "has_next": False}
    assert fake_service.list_articles_kwargs == {
        "article_type": ArticleType.blog,
        "keyword": "ai",
        "tag": "Python",
        "author": "lucan",
        "category": "tech",
        "has_issues": True,
        "page": 2,
        "page_size": 5,
        "sort": "-date",
    }


def test_list_articles_api_requires_auth_before_service_dependency(client: TestClient) -> None:
    fake_service = FakeArticleService()
    app.dependency_overrides[get_article_service] = lambda: fake_service

    response = client.get("/api/v1/articles")

    assert response.status_code == 401
    assert fake_service.list_articles_kwargs is None


def test_create_article_api_uses_article_workflow_dependency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_workflow = FakeArticleWorkflow()
    app.dependency_overrides[get_article_workflow_service] = lambda: fake_workflow
    response = client.post(
        "/api/v1/articles",
        json={
            "type": "docs",
            "title": "Test Article",
            "slug": "test",
            "category_path": ["docs"],
            "body": "Body",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["id"] == "docs:test.md"
    assert fake_workflow.payload is not None
    assert fake_workflow.payload.title == "Test Article"
    assert fake_workflow.payload.type == ArticleType.docs
