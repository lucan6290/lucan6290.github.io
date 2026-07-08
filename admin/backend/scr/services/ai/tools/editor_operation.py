"""Shared editor operation helpers."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import ValidationError

from scr.schemas.agent import EditorAgentOperationDTO, EditorAgentRunRequestDTO


def coerce_operation_data(operation_data: Any) -> Any:
    if not isinstance(operation_data, dict):
        return operation_data

    data = dict(operation_data)
    # 模型经常返回近义词，这里先归一化到 DTO 支持的枚举，再交给 Pydantic 严格校验。
    type_aliases = {
        "add": "insert",
        "append": "insert",
        "create": "insert",
        "edit": "replace",
        "modify": "replace",
        "update": "replace",
        "remove": "delete",
        "metadata": "frontmatter",
        "front_matter": "frontmatter",
        "frontMatter": "frontmatter",
    }
    scope_aliases = {
        "all": "document",
        "article": "document",
        "body": "document",
        "doc": "document",
        "full": "document",
        "whole": "document",
        "selected": "selection",
        "selected_text": "selection",
        "front_matter": "frontmatter",
        "metadata": "frontmatter",
    }
    insert_position_aliases = {
        "after": "after_old_text",
        "after_text": "after_old_text",
        "before": "before_old_text",
        "before_text": "before_old_text",
        "beginning": "prepend",
        "end": "append",
        "start": "prepend",
    }

    operation_type = data.get("type")
    if isinstance(operation_type, str):
        data["type"] = type_aliases.get(operation_type.strip(), operation_type.strip())

    scope = data.get("scope")
    if isinstance(scope, str):
        data["scope"] = scope_aliases.get(scope.strip(), scope.strip())

    insert_position = data.get("insertPosition", data.get("insert_position"))
    if isinstance(insert_position, str):
        data["insertPosition"] = insert_position_aliases.get(insert_position.strip(), insert_position.strip())
        data.pop("insert_position", None)

    return data


def parse_operation_data(operation_data: Any) -> EditorAgentOperationDTO:
    return EditorAgentOperationDTO.model_validate(coerce_operation_data(operation_data))


def format_operation_validation_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    field_labels = {
        "type": "type",
        "scope": "scope",
        "insertPosition": "insertPosition",
        "insert_position": "insertPosition",
    }
    for error in exc.errors():
        field = ".".join(str(item) for item in error.get("loc", [])) or "operation"
        label = field_labels.get(field, field)
        value = error.get("input")
        if value is None:
            messages.append(f"{label} 字段不合法。")
        else:
            messages.append(f"{label} 字段不合法：{value!r}。")
    return messages or ["模型返回的编辑操作格式不合法。"]


def normalize_operation(
    payload: EditorAgentRunRequestDTO,
    operation: EditorAgentOperationDTO,
    body: str,
) -> EditorAgentOperationDTO:
    selection_text = payload.selection.text if payload.selection else ""
    # 当模型只知道“替换选区”但没有准确填写 oldText 时，用前端选区文本补齐定位依据。
    if (
        selection_text
        and operation.scope == "selection"
        and operation.type in {"replace", "delete", "rewrite"}
        and operation.old_text not in body
        and selection_text in body
    ):
        return operation.model_copy(update={"old_text": selection_text})
    return operation


def apply_insert(body: str, operation: EditorAgentOperationDTO) -> str:
    if operation.new_text is None:
        raise ValueError("插入操作缺少 newText。")
    position = operation.insert_position or "append"
    if position == "prepend":
        return operation.new_text + ("\n\n" if body else "") + body
    if position == "append":
        return body + ("\n\n" if body else "") + operation.new_text
    if not operation.old_text:
        raise ValueError("before_old_text / after_old_text 插入需要 oldText。")
    index = body.find(operation.old_text)
    if index < 0:
        raise ValueError("未找到 oldText，无法定位插入位置。")
    insert_at = index if position == "before_old_text" else index + len(operation.old_text)
    return body[:insert_at] + operation.new_text + body[insert_at:]


def apply_replace(body: str, operation: EditorAgentOperationDTO) -> str:
    if not operation.old_text:
        raise ValueError("替换操作缺少 oldText。")
    if operation.new_text is None:
        raise ValueError("替换操作缺少 newText。")
    if operation.old_text not in body:
        raise ValueError("未找到 oldText，无法替换。")
    return body.replace(operation.old_text, operation.new_text, 1)


def apply_delete(body: str, operation: EditorAgentOperationDTO) -> str:
    if not operation.old_text:
        raise ValueError("删除操作缺少 oldText。")
    if operation.old_text not in body:
        raise ValueError("未找到 oldText，无法删除。")
    return body.replace(operation.old_text, "", 1)


def compute_risk_flags(operation: EditorAgentOperationDTO) -> list[str]:
    # 风险标记既接收模型判断，也在后端按操作类型补充硬规则，供审批策略统一消费。
    flags: list[str] = list(operation.risk_flags)
    if operation.type in {"delete", "frontmatter"}:
        flags.append("high-risk")
    if operation.type == "rewrite" and operation.scope == "document":
        flags.append("high-risk")
    if operation.type == "insert" and operation.scope in {"selection", "document"}:
        flags.append("low-risk")
    if operation.type == "replace" and operation.scope == "selection":
        flags.append("low-risk")
    return sorted(set(flags))


def policy_decision(
    *,
    approval_mode: str,
    operation: EditorAgentOperationDTO,
    risk_flags: list[str],
    confirmed: bool,
) -> str:
    # 写入策略集中在这里，避免 preview/write/API 各自判断导致审批行为不一致。
    if "blocked" in risk_flags:
        return "deny"
    if confirmed:
        return "allow"
    high_risk = "high-risk" in risk_flags or operation.type in {"delete", "frontmatter"} or (
        operation.type == "rewrite" and operation.scope == "document"
    )
    if approval_mode == "request-approval":
        return "ask"
    if approval_mode == "delegate-approval" and high_risk:
        return "ask"
    return "allow"


def editor_operation_properties() -> dict[str, Any]:
    return {
        "type": {"type": "string", "enum": ["insert", "replace", "delete", "rewrite", "frontmatter"]},
        "scope": {"type": "string", "enum": ["document", "selection", "frontmatter"]},
        "summary": {"type": "string"},
        "oldText": {"type": "string"},
        "newText": {"type": "string"},
        "insertPosition": {
            "type": "string",
            "enum": ["append", "prepend", "before_old_text", "after_old_text"],
        },
        "frontMatterPatch": {"type": "object", "additionalProperties": True},
        "riskFlags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    }


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
