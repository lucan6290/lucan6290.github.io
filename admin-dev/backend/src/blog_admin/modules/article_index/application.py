from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from blog_admin.core.response import fail, ok

from .article_index_cache import load_or_scan, scan_and_store
from .knowledge_retriever import (
    build_inventory_answer,
    citations_from_chunks,
    classify_question,
    retrieve_articles,
    retrieve_chunks,
)
from .schemas import AIModelConfig, ArticleIndexScanRequest, KnowledgeQARequest

COMMON_SYSTEM_PROMPT = """你是箓川码笺博客管理后台的 AI 写作助手。

你只能使用用户输入、当前文章内容、本地文章索引、分类注册表和系统明确提供的项目规则。
不得编造不存在的一级分类、二级前缀、文件路径、文章路径、接口能力、构建命令或项目配置。
不得声称你已经创建、保存、发布、删除、提交或修改文件；真实写入只能由后端接口完成。
必须区分“用户目的说明”和“文章正文素材”，不要把任务说明直接写进正文。
不确定时必须降低 confidence，并在 riskFlags、rationale 或 summary 中说明原因。
不得伪造或提升用户选择的 approvalMode。
遇到高风险、低置信度、求证未完成、图片占位不明确或作用范围不明确时，必须请求人工确认。
只能输出指定 JSON schema，不要输出 Markdown 代码块，不要输出解释文字。"""


def build_knowledge_prompt(context: dict[str, Any]) -> str:
    return f"""任务：基于系统提供的本地文章索引和正文分块回答用户问题。

你只能使用 evidence 中的文章、Front Matter、正文分块和引用来源。
不得使用模型记忆猜测用户写过哪些文章。
不得把通用知识当作用户文章中的内容。
找不到依据时，回答“当前文章中没有找到明确依据”。
回答具体内容问题时必须包含来源。
如果索引过期、扫描失败或引用校验失败，不得输出确定性结论。

上下文 JSON：
{json.dumps(context, ensure_ascii=False, indent=2)}
"""


def _has_model_config(config: AIModelConfig | None) -> bool:
    return bool(config and config.baseUrl and config.apiKey and config.modelId)


def _build_chat_model(config: AIModelConfig):
    from langchain_openai import ChatOpenAI

    is_deepseek = config.provider == "deepseek" or config.modelId.startswith("deepseek")
    thinking_enabled = is_deepseek and config.thinkingMode == "enabled"
    extra_body = {"thinking": {"type": config.thinkingMode}} if is_deepseek else None
    kwargs: dict[str, Any] = {
        "base_url": config.baseUrl,
        "api_key": config.apiKey,
        "model": config.modelId,
        "max_tokens": config.maxTokens,
        "streaming": False,
        "extra_body": extra_body,
    }
    if thinking_enabled:
        kwargs["reasoning_effort"] = config.reasoningEffort
    else:
        kwargs["temperature"] = config.temperature
    return ChatOpenAI(**kwargs)


async def scan_article_index(req: ArticleIndexScanRequest) -> dict[str, Any]:
    try:
        data = scan_and_store(include_drafts=req.includeDrafts)
        return ok({
            "scannedAt": data.get("scannedAt"),
            "articleCount": len(data.get("articles", [])),
            "draftCount": sum(1 for item in data.get("articles", []) if item.get("status") == "draft"),
            "indexStatus": data.get("indexStatus", "rebuilt"),
            "failedFiles": data.get("failedFiles", []),
            "stats": data.get("stats", {}),
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"扫描文章索引失败: {exc}") from exc


async def get_article_index(include_drafts: bool = True, auto_refresh: bool = True) -> dict[str, Any]:
    try:
        data = load_or_scan(include_drafts=include_drafts, force=False)
        return ok({
            "scannedAt": data.get("scannedAt"),
            "indexStatus": data.get("indexStatus"),
            "articles": data.get("articles", []),
            "stats": data.get("stats", {}),
            "failedFiles": data.get("failedFiles", []),
            "warnings": [],
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取文章索引失败: {exc}") from exc


async def knowledge_qa(req: KnowledgeQARequest) -> dict[str, Any]:
    if not req.question.strip():
        return fail("RESPONSE_ERROR", "问题不能为空")
    try:
        return ok(await run_knowledge_qa(req))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"知识库问答失败: {exc}") from exc


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
    model = req.model
    if not _has_model_config(model):
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

    assert model is not None
    llm = _build_chat_model(model)
    response = await llm.ainvoke([
        ("system", COMMON_SYSTEM_PROMPT),
        ("human", build_knowledge_prompt({
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

