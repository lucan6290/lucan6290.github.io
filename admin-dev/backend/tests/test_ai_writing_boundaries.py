from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from blog_admin.modules.ai import application, post_io
from blog_admin.modules.ai.schemas import (
    AgentCommitRequest,
    AIApprovalMode,
    AIDraftPlan,
    AIEditOperation,
    AIWritingGoal,
    EditApplyRequest,
)
from blog_admin.modules.ai.validation import validate_edit_operation
from blog_admin.modules.content import application as content_application


def _draft_plan() -> AIDraftPlan:
    return AIDraftPlan(
        approvalMode=AIApprovalMode.FULL_ACCESS,
        writingGoal=AIWritingGoal.BLOG_DRAFT,
        userIntent="写一篇测试文章",
        inputType="prompt",
        primarySlug="tech-study",
        primaryName="技术研习",
        prefix1="ts",
        prefix2="ai",
        title="AI 边界测试",
        tags=["AI"],
        description="这是一段用于测试 AI 写作边界的文章简介，长度足够用于通过基础校验。",
        outline=["背景", "实现", "总结"],
        bodyMarkdown="## 背景\n\n正文内容",
        confidence=0.95,
    )


def test_ai_post_io_create_update_read_delegate_to_content_application(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Any, ...]] = []

    async def fake_create_post(req: Any) -> dict[str, Any]:
        calls.append(("create", req))
        return {"success": True, "data": {"path": "tech-study/ts-ai-demo.md"}}

    async def fake_update_post(path: str, req: Any) -> dict[str, Any]:
        calls.append(("update", path, req))
        return {"success": True, "data": {"unusedImages": []}}

    async def fake_get_post(path: str) -> dict[str, Any]:
        calls.append(("read", path))
        return {
            "success": True,
            "data": {
                "frontMatter": {"title": "Demo"},
                "raw": "---\ntitle: Demo\n---\n正文",
            },
        }

    monkeypatch.setattr(content_application, "create_post", fake_create_post)
    monkeypatch.setattr(content_application, "update_post", fake_update_post)
    monkeypatch.setattr(content_application, "get_post", fake_get_post)

    create_result = asyncio.run(post_io.create_post_file("Demo", "ts", "ai"))
    update_result = asyncio.run(post_io.update_post_file("tech-study/ts-ai-demo.md", {"title": "Demo"}, "正文"))
    read_result = asyncio.run(post_io.read_post("tech-study/ts-ai-demo.md"))

    assert create_result["data"]["path"] == "tech-study/ts-ai-demo.md"
    assert update_result["success"] is True
    assert read_result == ("tech-study/ts-ai-demo.md", {"title": "Demo"}, "正文", "---\ntitle: Demo\n---\n正文")
    assert calls[0][0] == "create"
    assert calls[1][0] == "update"
    assert calls[2] == ("read", "tech-study/ts-ai-demo.md")


def test_agent_commit_writes_only_through_post_io_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Any, ...]] = []
    application._IDEMPOTENCY.clear()

    async def fake_create_post_file(title: str, prefix1: str, prefix2: str) -> dict[str, Any]:
        calls.append(("create", title, prefix1, prefix2))
        return {"success": True, "data": {"path": "tech-study/ts-ai-boundary.md"}}

    async def fake_update_post_file(path: str, front_matter_patch: dict[str, Any] | None, content: str | None) -> dict[str, Any]:
        calls.append(("update", path, front_matter_patch, content))
        return {"success": True, "data": {"unusedImages": []}}

    monkeypatch.setattr(application, "validate_draft_plan", lambda _plan: ([], []))
    monkeypatch.setattr(application, "can_auto_commit_plan", lambda _plan, _mode, _confirmed: (True, []))
    monkeypatch.setattr(application, "frontmatter_for_plan", lambda plan: {"title": plan.title})
    monkeypatch.setattr(application, "create_post_file", fake_create_post_file)
    monkeypatch.setattr(application, "update_post_file", fake_update_post_file)

    response = asyncio.run(
        application.agent_commit(
            AgentCommitRequest(
                sessionId="session-1",
                approvalMode=AIApprovalMode.FULL_ACCESS,
                confirmed=True,
                idempotencyKey="commit-boundary-1",
                plan=_draft_plan(),
            )
        )
    )

    assert response["success"] is True
    assert response["data"]["path"] == "tech-study/ts-ai-boundary.md"
    assert calls == [
        ("create", "AI 边界测试", "ts", "ai"),
        ("update", "tech-study/ts-ai-boundary.md", {"title": "AI 边界测试"}, "## 背景\n\n正文内容"),
    ]


def test_agent_commit_requires_confirmation_for_risky_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    application._IDEMPOTENCY.clear()
    create_called = False

    async def fake_create_post_file(_title: str, _prefix1: str, _prefix2: str) -> dict[str, Any]:
        nonlocal create_called
        create_called = True
        return {"success": True, "data": {"path": "tech-study/ts-ai-risk.md"}}

    monkeypatch.setattr(application, "validate_draft_plan", lambda _plan: ([], []))
    monkeypatch.setattr(application, "create_post_file", fake_create_post_file)

    plan = _draft_plan()
    plan.approvalMode = AIApprovalMode.REQUEST_APPROVAL
    plan.confidence = 0.2

    response = asyncio.run(
        application.agent_commit(
            AgentCommitRequest(
                sessionId="session-risk",
                approvalMode=AIApprovalMode.FULL_ACCESS,
                confirmed=False,
                idempotencyKey="commit-boundary-risk",
                plan=plan,
            )
        )
    )

    assert response["success"] is False
    assert response["error"]["code"] == "RISK_REQUIRES_APPROVAL"
    assert create_called is False


def test_edit_apply_writes_only_through_post_io_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Any, ...]] = []

    async def fake_read_post(path: str) -> tuple[str, dict[str, Any], str, str]:
        calls.append(("read", path))
        return path, {"title": "Demo"}, "原正文", "---\ntitle: Demo\n---\n原正文"

    async def fake_update_post_file(path: str, front_matter_patch: dict[str, Any] | None, content: str | None) -> dict[str, Any]:
        calls.append(("update", path, front_matter_patch, content))
        return {"success": True, "data": {"path": path, "unusedImages": []}}

    monkeypatch.setattr(application, "read_post", fake_read_post)
    monkeypatch.setattr(application, "update_post_file", fake_update_post_file)

    response = asyncio.run(
        application.edit_apply(
            EditApplyRequest(
                sessionId="edit-1",
                articlePath="tech-study/ts-ai-demo.md",
                approvalMode=AIApprovalMode.FULL_ACCESS,
                confirmed=True,
                operation=AIEditOperation(
                    type="insert",
                    scope="document",
                    approvalMode=AIApprovalMode.FULL_ACCESS,
                    requiresManualApproval=False,
                    summary="追加内容",
                    newText="新增段落",
                    confidence=0.95,
                ),
            )
        )
    )

    assert response["success"] is True
    assert calls == [
        ("read", "tech-study/ts-ai-demo.md"),
        ("update", "tech-study/ts-ai-demo.md", None, "原正文\n\n新增段落"),
    ]


def test_edit_validation_rejects_publishing_status_patch() -> None:
    errors, warnings = validate_edit_operation(
        AIEditOperation(
            type="frontmatter",
            scope="frontmatter",
            approvalMode=AIApprovalMode.FULL_ACCESS,
            requiresManualApproval=False,
            summary="发布文章",
            frontMatterPatch={"status": "published"},
            confidence=0.9,
        ),
        body="正文",
    )

    assert "AI 不能自动将文章状态改为 published" in errors
    assert warnings == []


def test_ai_module_has_no_direct_file_write_boundary() -> None:
    ai_root = Path(__file__).resolve().parents[1] / "src" / "blog_admin" / "modules" / "ai"
    forbidden_file_ops = (
        ".write_text(",
        ".write_bytes(",
        ".unlink(",
        ".mkdir(",
        "shutil.rmtree(",
        "open(",
    )
    offenders: list[str] = []

    for path in ai_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_file_ops:
            if pattern in text:
                offenders.append(f"{path.relative_to(ai_root).as_posix()}: {pattern}")
        if path.name != "post_io.py" and "from ..content import application as content_application" in text:
            offenders.append(f"{path.relative_to(ai_root).as_posix()}: direct content application import")

    assert not offenders, "AI module must write through post_io/content boundaries:\n" + "\n".join(offenders)
