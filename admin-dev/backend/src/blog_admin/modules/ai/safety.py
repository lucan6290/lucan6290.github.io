"""Permission and safety policy for AI writing."""
from __future__ import annotations

from collections.abc import Iterable

from .schemas import AIApprovalMode, AIDraftPlan, AIEditOperation

HIGH_RISK_FLAGS = {"分类不确定", "事实待验证", "信息不足", "可能包含敏感信息"}
def normalize_approval_mode(value: AIApprovalMode | str) -> AIApprovalMode:
    try:
        return AIApprovalMode(value)
    except ValueError:
        return AIApprovalMode.REQUEST_APPROVAL


def evaluate_plan_permission(
    plan: AIDraftPlan,
    requested: AIApprovalMode,
) -> tuple[AIApprovalMode, list[str]]:
    reasons: list[str] = []
    effective = normalize_approval_mode(requested)

    if plan.approvalMode != requested:
        reasons.append("AI 返回的权限模式与用户请求不一致，按用户请求处理")

    if plan.confidence < 0.6:
        reasons.append("置信度低于 0.6")
    if plan.clarificationRequired:
        reasons.append("仍存在未完成求证问题")
    risky = sorted(set(plan.riskFlags).intersection(HIGH_RISK_FLAGS))
    if risky:
        reasons.append("存在高风险标记: " + "、".join(risky))
    if any("图片" in flag and "不" in flag for flag in plan.riskFlags):
        reasons.append("图片占位不明确")

    if reasons:
        effective = AIApprovalMode.REQUEST_APPROVAL
    return effective, reasons


def can_auto_commit_plan(plan: AIDraftPlan, requested: AIApprovalMode, confirmed: bool) -> tuple[bool, list[str]]:
    effective, reasons = evaluate_plan_permission(plan, requested)
    if effective == AIApprovalMode.REQUEST_APPROVAL and not confirmed:
        reasons.append("当前权限需要用户确认后才能创建或写入")
        return False, reasons
    return True, reasons


def evaluate_edit_permission(
    operation: AIEditOperation,
    requested: AIApprovalMode,
    confirmed: bool,
) -> tuple[bool, AIApprovalMode, list[str]]:
    effective = normalize_approval_mode(requested)
    reasons: list[str] = []

    if operation.approvalMode != requested:
        reasons.append("AI 返回的权限模式与用户请求不一致，按用户请求处理")

    if operation.confidence < 0.6:
        reasons.append("编辑操作置信度低于 0.6")
    risky = sorted(set(operation.riskFlags).intersection(HIGH_RISK_FLAGS))
    if risky:
        reasons.append("存在高风险标记: " + "、".join(risky))
    if operation.type in {"delete", "rewrite"}:
        reasons.append("删除或全文重写需要人工确认")
    if operation.requiresManualApproval:
        reasons.append("编辑操作要求人工确认")

    if reasons:
        effective = AIApprovalMode.REQUEST_APPROVAL
    if effective == AIApprovalMode.REQUEST_APPROVAL and not confirmed:
        reasons.append("当前编辑需要用户确认后才能应用")
        return False, effective, reasons
    return True, effective, reasons


def contains_high_risk(flags: Iterable[str]) -> bool:
    return bool(set(flags).intersection(HIGH_RISK_FLAGS))
