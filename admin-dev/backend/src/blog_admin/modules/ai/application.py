"""Application services for AI chat and writing workflows."""
from __future__ import annotations

import json
import logging
import zipfile
from collections.abc import AsyncGenerator
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sse_starlette.sse import EventSourceResponse

from ...core.response import fail, ok
from ...core.schemas import ChatRequest, TestConnectionRequest
from ...core.settings import settings
from .graphs import run_agent_plan, run_edit_plan
from .models import build_chat_model, validate_model_config
from .post_io import create_post_file, frontmatter_for_plan, read_post, response_error, update_post_file
from .safety import can_auto_commit_plan, evaluate_edit_permission
from .schemas import (
    AgentCommitRequest,
    AgentPlanRequest,
    AIModelConfig,
    EditApplyRequest,
    EditPlanRequest,
)
from .validation import validate_draft_plan, validate_edit_operation

logger = logging.getLogger(__name__)

_IDEMPOTENCY: dict[str, dict[str, Any]] = {}
_MAX_MATERIAL_BYTES = 2 * 1024 * 1024


def _model_config_from_request(req: ChatRequest | TestConnectionRequest) -> AIModelConfig:
    return AIModelConfig(
        baseUrl=req.baseUrl,
        apiKey=req.apiKey,
        modelId=req.modelId,
        provider=req.provider,
        apiFormat=req.apiFormat if req.apiFormat in {"openai", "anthropic"} else "openai",
        anthropicBaseUrl=req.anthropicBaseUrl,
        thinkingMode=req.thinkingMode if req.thinkingMode in {"enabled", "disabled"} else "disabled",
        reasoningEffort=req.reasoningEffort if req.reasoningEffort in {"high", "max"} else "high",
        agentMode=req.agentMode,
        toolCalls=req.toolCalls,
        strictToolCalls=req.strictToolCalls,
        jsonMode=req.jsonMode,
        temperature=req.temperature,
        maxTokens=req.maxTokens,
    )


def _extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        try:
            document_xml = archive.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("无法读取 docx 正文内容") from exc

    root = ElementTree.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{{{namespace['w']}}}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{{{namespace['w']}}}tab":
                parts.append("\t")
            elif node.tag == f"{{{namespace['w']}}}br":
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


async def get_presets() -> Any:
    return ok(settings.model_presets)


async def test_connection(req: TestConnectionRequest) -> Any:
    try:
        config = _model_config_from_request(req)
        config.maxTokens = 5
        llm = build_chat_model(config)
        response = await llm.ainvoke([HumanMessage(content="Hi")])
        return ok({"content": response.content})
    except Exception as exc:
        logger.warning("AI 连接测试失败: %s", exc)
        return fail("AI_CONNECTION_FAILED", f"连接失败: {exc}")


async def chat(req: ChatRequest) -> Any:
    if not req.baseUrl or not req.apiKey or not req.modelId:
        return fail("AI_MODEL_CONFIG_INVALID", "请提供完整的模型配置（baseUrl / apiKey / modelId）")

    lc_messages = []
    for msg in req.messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
        else:
            lc_messages.append(HumanMessage(content=msg.content))

    llm = build_chat_model(_model_config_from_request(req), streaming=True)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            async for chunk in llm.astream(lc_messages):
                content = chunk.content
                if content:
                    data = json.dumps(
                        {"choices": [{"delta": {"content": content}}]},
                        ensure_ascii=False,
                    )
                    yield {"event": "message", "data": data}
            yield {"event": "message", "data": "[DONE]"}
        except Exception as exc:
            logger.error("AI 生成失败: %s", exc)
            error_data = json.dumps({"error": f"生成失败: {exc}"}, ensure_ascii=False)
            yield {"event": "message", "data": error_data}
            yield {"event": "message", "data": "[DONE]"}

    return EventSourceResponse(event_generator())


async def extract_material(file) -> Any:
    filename = file.filename or "material"
    suffix = Path(filename).suffix.lower()
    content = await file.read()
    if len(content) > _MAX_MATERIAL_BYTES:
        return fail("AI_MATERIAL_TOO_LARGE", "素材文件过大，请控制在 2MB 以内")

    try:
        if suffix == ".docx":
            text = _extract_docx_text(content)
        elif suffix in {".md", ".markdown", ".txt", ".text", ".log"}:
            text = content.decode("utf-8-sig")
        else:
            return fail("AI_MATERIAL_UNSUPPORTED", "仅支持 md、txt、log、docx 素材文件")
    except UnicodeDecodeError:
        return fail("AI_MATERIAL_ENCODING_INVALID", "文本编码无法识别，请保存为 UTF-8 后重试")
    except (zipfile.BadZipFile, ElementTree.ParseError, ValueError) as exc:
        return fail("AI_MATERIAL_PARSE_FAILED", f"素材解析失败: {exc}")

    text = text.strip()
    if not text:
        return fail("AI_MATERIAL_EMPTY", "素材文件没有可读取的文本内容")
    return ok({
        "filename": filename,
        "content": text,
        "contentType": suffix.removeprefix(".") or "text",
        "warnings": [],
    })


async def agent_plan(req: AgentPlanRequest) -> Any:
    if not req.userInput.strip():
        return fail("VALIDATION_ERROR", "输入内容不能为空")
    model_error = validate_model_config(req.model)
    if model_error:
        return fail("AI_MODEL_CONFIG_INVALID", model_error)
    try:
        data = await run_agent_plan(req)
        if data.get("validationErrors"):
            return fail("AI_SCHEMA_INVALID", "草稿方案校验失败", details=data)
        return ok(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成草稿方案失败: {exc}") from exc


async def agent_commit(req: AgentCommitRequest) -> Any:
    if req.idempotencyKey in _IDEMPOTENCY:
        return ok(_IDEMPOTENCY[req.idempotencyKey])

    validation_errors, warnings = validate_draft_plan(req.plan)
    if validation_errors:
        return fail(
            "AI_SCHEMA_INVALID",
            "草稿方案校验失败",
            details={
                "validationErrors": validation_errors,
                "warnings": warnings,
                "sessionId": req.sessionId,
            },
        )

    allowed, reasons = can_auto_commit_plan(req.plan, req.approvalMode, req.confirmed)
    if not allowed:
        return fail(
            "RISK_REQUIRES_APPROVAL",
            "当前方案需要用户确认后才能写入",
            details={
                "downgradeReasons": reasons,
                "sessionId": req.sessionId,
            },
        )

    create_result = await create_post_file(req.plan.title, req.plan.prefix1, req.plan.prefix2)
    if not create_result.get("success"):
        return fail(
            "POST_CREATE_FAILED",
            response_error(create_result, "创建文章失败"),
            details={
                "warnings": warnings,
                "sessionId": req.sessionId,
            },
        )

    created_path = create_result["data"]["path"]
    write_result = await update_post_file(created_path, frontmatter_for_plan(req.plan), req.plan.bodyMarkdown)
    if not write_result.get("success"):
        data = {
            "path": created_path,
            "created": True,
            "written": False,
            "code": "POST_WRITE_FAILED",
            "error": response_error(write_result, "写入正文失败"),
            "warnings": warnings,
        }
        _IDEMPOTENCY[req.idempotencyKey] = data
        return fail("POST_WRITE_FAILED", response_error(write_result, "写入正文失败"), details=data)

    data = {
        "path": created_path,
        "created": True,
        "written": True,
        "editorUrl": f"/editor?file={created_path.replace('/', '%2F')}",
        "warnings": warnings,
        "unusedImages": write_result.get("data", {}).get("unusedImages", []),
    }
    _IDEMPOTENCY[req.idempotencyKey] = data
    return ok(data)


async def edit_plan(req: EditPlanRequest) -> Any:
    if not req.instruction.strip():
        return fail("VALIDATION_ERROR", "修改指令不能为空")
    model_error = validate_model_config(req.model)
    if model_error:
        return fail("AI_MODEL_CONFIG_INVALID", model_error)
    try:
        data = await run_edit_plan(req)
        if data.get("validationErrors"):
            return fail("AI_SCHEMA_INVALID", "编辑方案校验失败", details=data)
        return ok(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成编辑方案失败: {exc}") from exc


async def edit_apply(req: EditApplyRequest) -> Any:
    post = await read_post(req.articlePath)
    if not post:
        return fail("POST_NOT_FOUND", "文章不存在")
    _path, _fm, body, _raw = post
    selection_text = req.operation.oldText or ""
    validation_errors, warnings = validate_edit_operation(req.operation, body=body, selection_text=selection_text)
    if validation_errors:
        return fail(
            "AI_SCHEMA_INVALID",
            "编辑操作校验失败",
            details={
                "validationErrors": validation_errors,
                "warnings": warnings,
            },
        )

    allowed, effective, reasons = evaluate_edit_permission(req.operation, req.approvalMode, req.confirmed)
    if not allowed:
        return fail(
            "RISK_REQUIRES_APPROVAL",
            "当前编辑需要用户确认后才能应用",
            details={
                "approvalModeEffective": effective.value,
                "downgradeReasons": reasons,
            },
        )

    new_body = body
    frontmatter_patch = None
    op = req.operation
    if op.type == "insert":
        new_body = body + ("\n\n" if body and not body.endswith("\n") else "") + (op.newText or "")
    elif op.type == "replace":
        if not op.oldText or op.oldText not in body:
            return fail("EDIT_CONFLICT", "原文已变化，无法应用替换")
        new_body = body.replace(op.oldText, op.newText or "", 1)
    elif op.type == "delete":
        if not op.oldText or op.oldText not in body:
            return fail("EDIT_CONFLICT", "原文已变化，无法应用删除")
        new_body = body.replace(op.oldText, "", 1)
    elif op.type == "rewrite":
        new_body = op.newText or ""
    elif op.type == "frontmatter":
        frontmatter_patch = op.frontMatterPatch or {}

    result = await update_post_file(req.articlePath, frontmatter_patch, new_body)
    if not result.get("success"):
        return fail("POST_WRITE_FAILED", response_error(result, "保存文章失败"))
    return ok(result.get("data"))

