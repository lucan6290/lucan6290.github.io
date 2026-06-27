"""LangChain/LangGraph orchestration helpers for AI writing."""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage

from ..article_index.article_index_cache import load_or_scan
from ..article_index.knowledge_retriever import (
    build_inventory_answer,
    citations_from_chunks,
    classify_question,
    retrieve_articles,
    retrieve_chunks,
)
from .models import build_chat_model
from .post_io import read_post
from .prompts import (
    COMMON_SYSTEM_PROMPT,
    build_agent_plan_prompt,
    build_edit_prompt,
    build_json_repair_prompt,
    build_knowledge_prompt,
)
from .safety import evaluate_plan_permission
from .schemas import (
    AgentPlanRequest,
    AIDraftPlan,
    AIEditOperation,
    EditPlanRequest,
    KnowledgeQARequest,
)
from .validation import (
    build_preview,
    get_category_registry,
    parse_model_json,
    validate_draft_plan,
    validate_edit_operation,
)

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    END = None
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


def _existing_prefixes(articles: list[dict[str, Any]]) -> dict[str, list[str]]:
    prefixes: dict[str, set[str]] = {}
    for article in articles:
        file_name = str(article.get("fileName", ""))
        parts = file_name.removesuffix(".md").split("-", 2)
        if len(parts) >= 2:
            prefixes.setdefault(parts[0], set()).add(parts[1])
    return {key: sorted(value) for key, value in prefixes.items()}


def _compact_conversation_history(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    compacted: list[dict[str, str]] = []
    for message in messages[-8:]:
        role = message.get("role", "")
        if role not in {"user", "assistant"}:
            continue
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        compacted.append({
            "role": role,
            "content": content[:1200],
        })
    return compacted


async def _repair_json_once(model_config: Any, raw_text: str, schema_name: str, schema_model: Any) -> tuple[Any | None, list[str]]:
    parsed, errors = parse_model_json(schema_model, raw_text)
    if parsed:
        return parsed, []
    llm = build_chat_model(model_config, json_mode=True)
    response = await llm.ainvoke([
        SystemMessage(content=COMMON_SYSTEM_PROMPT),
        HumanMessage(content=build_json_repair_prompt(raw_text, schema_name)),
    ])
    repaired, repair_errors = parse_model_json(schema_model, str(response.content))
    return repaired, errors + repair_errors


async def _agent_plan_pipeline(req: AgentPlanRequest) -> dict[str, Any]:
    session_id = req.sessionId or str(uuid4())
    index = load_or_scan(include_drafts=True, force=False)
    articles = index.get("articles", [])
    context = {
        "sessionId": session_id,
        "userInput": req.userInput,
        "conversationHistory": _compact_conversation_history(req.conversationHistory),
        "approvalMode": req.approvalMode.value,
        "writingGoal": req.writingGoal.value,
        "userPreferences": req.userPreferences,
        "clarificationAnswers": req.clarificationAnswers,
        "categoryRegistry": [item.model_dump() for item in get_category_registry()],
        "existingPrefixes": _existing_prefixes(articles),
        "existingArticles": [
            {
                "title": item.get("title"),
                "path": item.get("path"),
                "categories": item.get("categories"),
                "tags": item.get("tags"),
                "status": item.get("status"),
            }
            for item in articles[:80]
        ],
    }
    llm = build_chat_model(req.model, json_mode=True)
    response = await llm.ainvoke([
        SystemMessage(content=COMMON_SYSTEM_PROMPT),
        HumanMessage(content=build_agent_plan_prompt(context)),
    ])
    plan, parse_errors = await _repair_json_once(req.model, str(response.content), "AIDraftPlan", AIDraftPlan)
    if not plan:
        return {
            "sessionId": session_id,
            "plan": None,
            "preview": None,
            "validationErrors": parse_errors,
            "warnings": [],
        }
    validation_errors, warnings = validate_draft_plan(plan)
    effective, downgrade_reasons = evaluate_plan_permission(plan, req.approvalMode)
    preview = build_preview(plan)
    preview.update({
        "requiresManualApproval": effective.value == "request-approval",
        "approvalModeEffective": effective.value,
        "downgradeReasons": downgrade_reasons,
    })
    return {
        "sessionId": session_id,
        "plan": plan.model_dump(),
        "preview": preview,
        "validationErrors": validation_errors,
        "warnings": warnings,
    }


async def run_agent_plan(req: AgentPlanRequest) -> dict[str, Any]:
    if not LANGGRAPH_AVAILABLE:
        return await _agent_plan_pipeline(req)

    async def plan_node(state: dict[str, Any]) -> dict[str, Any]:
        state.update(await _agent_plan_pipeline(req))
        return state

    graph = StateGraph(dict)
    graph.add_node("collect_context", lambda state: state)
    graph.add_node("plan_draft", plan_node)
    graph.add_edge("collect_context", "plan_draft")
    graph.add_edge("plan_draft", END)
    graph.set_entry_point("collect_context")
    compiled = graph.compile()
    return await compiled.ainvoke({"sessionId": req.sessionId or str(uuid4())})


async def run_edit_plan(req: EditPlanRequest) -> dict[str, Any]:
    session_id = req.sessionId or str(uuid4())
    post = await read_post(req.articlePath)
    if not post:
        return {"sessionId": session_id, "operation": None, "validationErrors": ["文章不存在"], "warnings": []}
    _path, fm, body, _raw = post
    selection_text = req.selection.text if req.selection else ""
    context = {
        "sessionId": session_id,
        "articlePath": req.articlePath,
        "frontMatter": fm,
        "body": body,
        "instruction": req.instruction,
        "approvalMode": req.approvalMode.value,
        "scope": req.scope,
        "selection": req.selection.model_dump() if req.selection else None,
    }
    llm = build_chat_model(req.model, json_mode=True)
    response = await llm.ainvoke([
        SystemMessage(content=COMMON_SYSTEM_PROMPT),
        HumanMessage(content=build_edit_prompt(context)),
    ])
    operation, parse_errors = await _repair_json_once(req.model, str(response.content), "AIEditOperation", AIEditOperation)
    if not operation:
        return {"sessionId": session_id, "operation": None, "validationErrors": parse_errors, "warnings": []}
    validation_errors, warnings = validate_edit_operation(operation, body=body, selection_text=selection_text)
    return {
        "sessionId": session_id,
        "operation": operation.model_dump(),
        "validationErrors": validation_errors,
        "warnings": warnings,
    }


async def run_knowledge_qa(req: KnowledgeQARequest) -> dict[str, Any]:
    session_id = req.sessionId or str(uuid4())
    index = load_or_scan(include_drafts=req.includeDrafts, force=req.forceRescan)
    articles = index.get("articles", [])
    chunks = index.get("chunks", [])
    question_type = classify_question(req.question)
    warnings = list(index.get("failedFiles", []))

    if question_type == "inventory":
        return {
            "sessionId": session_id,
            "questionType": question_type,
            "scannedAt": index.get("scannedAt"),
            "answer": build_inventory_answer(articles, str(index.get("scannedAt"))),
            "citations": [],
            "warnings": warnings,
        }

    matched_articles = retrieve_articles(req.question, articles)
    matched_chunks = retrieve_chunks(req.question, chunks)
    citations = citations_from_chunks(matched_chunks)
    if not matched_articles and not matched_chunks:
        return {
            "sessionId": session_id,
            "questionType": question_type,
            "scannedAt": index.get("scannedAt"),
            "answer": "当前文章中没有找到明确依据。",
            "citations": [],
            "warnings": warnings,
        }

    evidence = {
        "articles": matched_articles[:8],
        "chunks": matched_chunks[:8],
        "citations": citations,
    }
    if not req.model or not req.model.baseUrl or not req.model.apiKey or not req.model.modelId:
        snippets = "\n\n".join(
            f"来源：{chunk.get('articleTitle')}（{chunk.get('articlePath')}）\n{str(chunk.get('text', ''))[:360]}"
            for chunk in matched_chunks[:4]
        )
        answer = snippets or "已找到相关文章，但未配置模型，无法生成总结。"
        return {
            "sessionId": session_id,
            "questionType": question_type,
            "scannedAt": index.get("scannedAt"),
            "answer": answer,
            "citations": citations,
            "warnings": warnings + [{"message": "未配置模型，返回检索片段"}],
        }

    llm = build_chat_model(req.model)
    response = await llm.ainvoke([
        SystemMessage(content=COMMON_SYSTEM_PROMPT),
        HumanMessage(content=build_knowledge_prompt({
            "question": req.question,
            "questionType": question_type,
            "scannedAt": index.get("scannedAt"),
            "evidence": evidence,
        })),
    ])
    return {
        "sessionId": session_id,
        "questionType": question_type,
        "scannedAt": index.get("scannedAt"),
        "answer": str(response.content),
        "citations": citations,
        "warnings": warnings,
    }
