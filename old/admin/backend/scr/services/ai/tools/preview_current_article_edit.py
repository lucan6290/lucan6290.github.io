"""Tool: preview an edit operation against the current article."""

from __future__ import annotations

import difflib
import json
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field

from scr.schemas.agent import EditorAgentOperationDTO
from scr.services.ai.tools.editor_operation import (
    apply_delete,
    apply_insert,
    apply_replace,
    compute_risk_flags,
    editor_operation_properties,
    stable_hash,
)


class PreviewCurrentArticleEditInput(BaseModel):
    operation: dict[str, Any] = Field(..., description="EditorAgentOperation 对象。")


def preview_current_article_edit(
    *,
    body: str,
    frontmatter: dict[str, Any],
    operation: EditorAgentOperationDTO,
    current_hash: str,
) -> dict[str, Any]:
    validation_errors: list[str] = []
    risk_flags = compute_risk_flags(operation)
    # 预览阶段只修改副本，确保校验、diff、审批前不会碰真实文章文件。
    next_frontmatter = deepcopy(frontmatter)
    next_body = body

    try:
        if operation.type == "frontmatter":
            if not operation.front_matter_patch:
                validation_errors.append("frontmatter 操作缺少 frontMatterPatch。")
            else:
                next_frontmatter.update(operation.front_matter_patch)
        elif operation.type == "insert":
            next_body = apply_insert(body, operation)
        elif operation.type == "replace":
            next_body = apply_replace(body, operation)
        elif operation.type == "delete":
            next_body = apply_delete(body, operation)
        elif operation.type == "rewrite":
            if operation.scope != "document":
                next_body = apply_replace(body, operation)
            elif operation.new_text is None:
                validation_errors.append("全文重写缺少 newText。")
            else:
                next_body = operation.new_text
    except ValueError as exc:
        validation_errors.append(str(exc))

    diff = "\n".join(
        difflib.unified_diff(
            body.splitlines(),
            next_body.splitlines(),
            fromfile="before.md",
            tofile="after.md",
            lineterm="",
        )
    )
    return {
        "beforeHash": current_hash,
        # afterHash 覆盖 frontmatter 与正文，前端可用它判断预览内容是否仍对应当前编辑结果。
        "afterHash": stable_hash(json.dumps(next_frontmatter, ensure_ascii=False, sort_keys=True) + "\n" + next_body),
        "diff": diff,
        "riskFlags": risk_flags,
        "validationErrors": validation_errors,
        "frontmatter": next_frontmatter,
        "body": next_body,
    }


def preview_current_article_edit_schema() -> dict[str, Any]:
    operation_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": editor_operation_properties(),
        "required": ["type", "scope", "summary", "riskFlags", "confidence"],
    }
    return {
        "type": "function",
        "function": {
            "name": "preview_current_article_edit",
            "description": "根据 operation 预览当前文章修改，返回 diff、风险和校验错误。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"operation": operation_schema},
                "required": ["operation"],
            },
        },
    }


def create_preview_current_article_edit_tool(runtime: Any) -> Any:
    from langchain.tools import tool

    def _run(operation: dict[str, Any]) -> dict[str, Any]:
        """根据 EditorAgentOperation 预览当前文章修改，返回 diff、风险和校验错误。"""
        return runtime.preview_current_article_edit(operation)

    return tool(
        "preview_current_article_edit",
        description="根据 EditorAgentOperation 预览当前文章修改，返回 diff、风险和校验错误。",
        args_schema=PreviewCurrentArticleEditInput,
    )(_run)
