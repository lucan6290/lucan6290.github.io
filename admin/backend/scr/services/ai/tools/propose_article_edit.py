"""Tool schema: ask the model to propose an editor operation."""

from __future__ import annotations

from typing import Any

from scr.services.ai.tools.editor_operation import editor_operation_properties


def editor_operation_tool_schema(tool_name: str = "propose_article_edit") -> dict[str, Any]:
    # 这个 schema 是模型输出的第一道约束；真正的业务校验仍在 preview/write 阶段完成。
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": "为当前博客文章生成一个待后端预览和校验的编辑操作。不要直接写入文件。",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": editor_operation_properties(),
                "required": ["type", "scope", "summary", "riskFlags", "confidence"],
            },
        },
    }
