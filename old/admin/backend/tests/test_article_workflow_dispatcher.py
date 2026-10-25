from typing import cast

from scr.application.content.workflows.article_workflow import ArticleWorkflowService
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO


class RecordingWorkflow:
    def __init__(self) -> None:
        self.calls: list[ArticleCreateDTO] = []
        self.result = cast(ArticleDetailDTO, object())

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        self.calls.append(payload)
        return self.result


def test_article_workflow_dispatches_docs_creation_to_docs_workflow() -> None:
    docs_workflow = RecordingWorkflow()
    blog_workflow = RecordingWorkflow()
    payload = ArticleCreateDTO(type=ArticleType.docs, title="Doc", slug="doc", category_path=["docs"])

    result = ArticleWorkflowService(
        docs_workflow=docs_workflow,
        blog_workflow=blog_workflow,
    ).create_article(payload)

    assert result is docs_workflow.result
    assert docs_workflow.calls == [payload]
    assert blog_workflow.calls == []


def test_article_workflow_dispatches_blog_creation_to_blog_workflow() -> None:
    docs_workflow = RecordingWorkflow()
    blog_workflow = RecordingWorkflow()
    payload = ArticleCreateDTO(
        type=ArticleType.blog,
        title="Blog",
        slug="blog",
        category_path=["notes"],
        authors=["lucan"],
    )

    result = ArticleWorkflowService(
        docs_workflow=docs_workflow,
        blog_workflow=blog_workflow,
    ).create_article(payload)

    assert result is blog_workflow.result
    assert docs_workflow.calls == []
    assert blog_workflow.calls == [payload]
