"""Tool: read the current editor selection."""

from __future__ import annotations

from typing import Any

from scr.schemas.agent import EditorAgentRunRequestDTO


def get_current_selection(payload: EditorAgentRunRequestDTO) -> dict[str, Any]:
    return {"selection": payload.selection.model_dump(by_alias=True) if payload.selection else None}


def create_get_current_selection_tool(runtime: Any) -> Any:
    from langchain.tools import tool

    def _run() -> dict[str, Any]:
        """读取当前编辑器选区。没有选区时返回 null。"""
        return runtime.get_current_selection()

    return tool(
        "get_current_selection",
        description="读取当前编辑器选区。没有选区时返回 null。",
    )(_run)
