"""
AI / LangChain 路由
POST /api/ai/chat          — 流式对话（SSE）
GET  /api/ai/presets        — 获取模型预设列表
POST /api/ai/test           — 测试模型连接
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sse_starlette.sse import EventSourceResponse

from ..config import MODEL_PRESETS
from ..schemas import ApiResponse, ChatRequest, TestConnectionRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


# ============================================================
# 模型预设
# ============================================================

@router.get("/presets")
async def get_presets():
    """获取内置 AI 模型预设列表"""
    return ApiResponse(success=True, data=MODEL_PRESETS)


# ============================================================
# 连接测试
# ============================================================

@router.post("/test")
async def test_connection(req: TestConnectionRequest):
    """测试 AI 模型连接"""
    try:
        llm = ChatOpenAI(
            base_url=req.baseUrl,
            api_key=req.apiKey,
            model=req.modelId,
            max_tokens=5,
        )
        response = await llm.ainvoke([HumanMessage(content="Hi")])
        return ApiResponse(success=True, data={"content": response.content})
    except Exception as e:
        logger.warning("AI 连接测试失败: %s", e)
        return ApiResponse(success=False, error=f"连接失败: {e}")


# ============================================================
# 流式对话
# ============================================================

@router.post("/chat")
async def chat(req: ChatRequest):
    """
    AI 对话（流式 SSE 输出）
    前端用 EventSource 或 fetch + ReadableStream 消费。
    SSE 事件格式与 OpenAI Chat Completion API 兼容：
        data: {"choices": [{"delta": {"content": "..."}}]}
        data: [DONE]
    """
    if not req.baseUrl or not req.apiKey or not req.modelId:
        return ApiResponse(success=False, error="请提供完整的模型配置（baseUrl / apiKey / modelId）")

    # 构建 LangChain 消息列表
    lc_messages = []
    for msg in req.messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
        else:
            lc_messages.append(HumanMessage(content=msg.content))

    # 创建 LangChain ChatOpenAI 实例
    llm = ChatOpenAI(
        base_url=req.baseUrl,
        api_key=req.apiKey,
        model=req.modelId,
        streaming=True,
        temperature=req.temperature,
        max_tokens=req.maxTokens,
    )

    async def event_generator() -> AsyncGenerator[dict, None]:
        """生成 SSE 事件流"""
        try:
            async for chunk in llm.astream(lc_messages):
                content = chunk.content
                if content:
                    # 兼容 OpenAI SSE 格式
                    data = json.dumps(
                        {"choices": [{"delta": {"content": content}}]},
                        ensure_ascii=False,
                    )
                    yield {"event": "message", "data": data}

            # 结束标记
            yield {"event": "message", "data": "[DONE]"}
        except Exception as e:
            logger.error("AI 生成失败: %s", e)
            error_data = json.dumps(
                {"error": f"生成失败: {e}"},
                ensure_ascii=False,
            )
            yield {"event": "message", "data": error_data}
            yield {"event": "message", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
