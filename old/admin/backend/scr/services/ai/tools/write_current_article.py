"""Tool: validate and write the current article edit."""

from __future__ import annotations

from typing import Any

from scr.core.exceptions import BadRequestError, ConflictError
from scr.schemas.agent import EditorAgentOperationDTO
from scr.schemas.article import ArticleUpdateDTO
from scr.services.ai.tools.editor_operation import policy_decision
from scr.services.ai.tools.preview_current_article_edit import preview_current_article_edit


def write_current_article(
    *,
    article_service: Any,
    article: Any,
    operation: EditorAgentOperationDTO,
    expected_content_hash: str | None,
    approval_mode: str,
    confirmed: bool,
) -> dict[str, Any]:
    if not expected_content_hash:
        raise BadRequestError("缺少 expectedContentHash。", code="agent_expected_hash_required")
    # 乐观锁：只允许写入用户生成方案时看到的那一版文章，防止覆盖编辑器里的新改动。
    if expected_content_hash != article.version:
        raise ConflictError(
            "文章内容已变化，请重新生成编辑方案。",
            code="agent_content_hash_conflict",
            details={"expected_content_hash": expected_content_hash, "current_content_hash": article.version},
        )

    preview = preview_current_article_edit(
        body=article.body,
        frontmatter=article.frontmatter,
        operation=operation,
        current_hash=article.version,
    )
    if preview["validationErrors"]:
        raise BadRequestError("编辑操作不合法。", code="agent_operation_invalid", details={"errors": preview["validationErrors"]})

    # 统一复用预览结果做风险判断；只有 allow 才会真正调用文章保存服务。
    decision = policy_decision(
        approval_mode=approval_mode,
        operation=operation,
        risk_flags=preview["riskFlags"],
        confirmed=confirmed,
    )
    if decision == "ask":
        return {"status": "waiting_approval", "preview": preview}
    if decision == "deny":
        raise BadRequestError("当前编辑风险过高，已阻断写入。", code="agent_operation_blocked", details={"riskFlags": preview["riskFlags"]})

    saved = article_service.save_article(
        article.id,
        ArticleUpdateDTO(
            frontmatter=preview["frontmatter"],
            body=preview["body"],
            validate_after_save=True,
            expected_version=article.version,
        ),
    )
    return {
        "status": "completed",
        "saved": True,
        "articleId": saved.id,
        "latestContentHash": saved.version,
        "indexSyncStatus": "updated",
        "preview": preview,
    }
