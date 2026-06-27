"""Schema and business validation for AI generated outputs."""
from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..categories.registry import find_secondary_by_prefix, load_category_registry
from .schemas import AIDraftPlan, AIEditOperation, CategoryRegistryItem

T = TypeVar("T", bound=BaseModel)


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def parse_model_json(model: type[T], text: str) -> tuple[T | None, list[str]]:
    try:
        payload = extract_json_object(text)
        return model.model_validate(payload), []
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        return None, [str(exc)]


def get_category_registry() -> list[CategoryRegistryItem]:
    return [
        CategoryRegistryItem.model_validate(item)
        for item in load_category_registry(include_compat=True)
    ]


def validate_draft_plan(plan: AIDraftPlan) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    registry = {item.prefix1: item for item in get_category_registry()}
    by_slug = {item.primarySlug: item for item in registry.values()}

    item = by_slug.get(plan.primarySlug)
    if not item:
        errors.append(f"一级分类不可用: {plan.primarySlug}")
    else:
        if plan.primaryName != item.primaryName:
            errors.append(f"一级分类中文名不匹配，应为 {item.primaryName}")
        if plan.prefix1 != item.prefix1:
            errors.append(f"一级前缀不匹配，应为 {item.prefix1}")

    if plan.prefix1 not in registry:
        errors.append(f"一级前缀不可用: {plan.prefix1}")
    if not plan.prefix2:
        errors.append("二级前缀不能为空")
    if "-" in plan.prefix2:
        errors.append("二级前缀不能包含连字符 -")
    if not re.fullmatch(r"[A-Za-z0-9_]+", plan.prefix2):
        warnings.append("二级前缀建议只使用英文、数字或下划线")
    if plan.prefix1 and plan.prefix2 and not find_secondary_by_prefix(plan.prefix1, plan.prefix2):
        errors.append(f"二级前缀不属于当前一级分类: {plan.prefix1}-{plan.prefix2}")
    if not plan.title.strip():
        errors.append("文章标题不能为空")
    if not plan.description.strip():
        errors.append("文章简介不能为空")
    elif not (50 <= len(plan.description) <= 240):
        warnings.append("文章简介建议控制在 100 到 200 字")
    if not plan.bodyMarkdown.strip():
        errors.append("正文 Markdown 不能为空")
    if re.search(r"(^|\n)---\s*(\n|$)", plan.bodyMarkdown):
        errors.append("正文 Markdown 不能包含 Front Matter 分隔符 ---")
    if len(plan.clarificationQuestions) > 3:
        errors.append("求证问题最多 3 个")
    return errors, warnings


ALLOWED_FRONTMATTER_PATCH_FIELDS = {
    "title",
    "description",
    "tags",
    "categories",
    "series",
    "series_order",
    "excerpt",
    "slug",
    "status",
}


def validate_edit_operation(
    operation: AIEditOperation,
    *,
    body: str,
    selection_text: str = "",
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scope_text = selection_text if operation.scope == "selection" else body

    if operation.type == "insert" and not (operation.newText or "").strip():
        errors.append("插入操作必须包含 newText")
    if operation.type == "replace":
        if not operation.oldText:
            errors.append("替换操作必须包含 oldText")
        elif operation.oldText not in scope_text:
            errors.append("oldText 不在当前作用范围内")
        if not (operation.newText or "").strip():
            errors.append("替换操作必须包含 newText")
    if operation.type == "delete":
        if not operation.oldText:
            errors.append("删除操作必须包含 oldText")
        elif operation.oldText not in scope_text:
            errors.append("oldText 不在当前作用范围内")
        warnings.append("删除操作需要人工确认")
    if operation.type == "rewrite":
        if not (operation.newText or "").strip():
            errors.append("全文重写必须包含 newText")
        warnings.append("全文重写需要人工确认")
    if operation.type == "frontmatter":
        patch = operation.frontMatterPatch or {}
        invalid = sorted(set(patch) - ALLOWED_FRONTMATTER_PATCH_FIELDS)
        if invalid:
            errors.append("Front Matter 不允许修改字段: " + "、".join(invalid))
        if "status" in patch and patch.get("status") == "published":
            errors.append("AI 不能自动将文章状态改为 published")

    return errors, warnings


def build_preview(plan: AIDraftPlan) -> dict[str, Any]:
    registry = {item.prefix1: item for item in get_category_registry()}
    item = registry.get(plan.prefix1)
    primary_slug = item.primarySlug if item else plan.primarySlug
    file_name = f"{plan.prefix1}-{plan.prefix2}-{plan.title}.md"
    relative_path = f"{primary_slug}/{file_name}"
    return {
        "fileName": file_name,
        "relativePath": relative_path,
        "sourcePath": f"source/_posts/{relative_path}",
    }
