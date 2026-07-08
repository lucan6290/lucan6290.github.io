"""Editor Agent tool exposure."""

from __future__ import annotations

from typing import Any

from scr.services.ai.tools.get_current_selection import create_get_current_selection_tool
from scr.services.ai.tools.preview_current_article_edit import create_preview_current_article_edit_tool
from scr.services.ai.tools.read_current_article import create_read_current_article_tool


EDITOR_AGENT_PLAN_TOOL_NAMES = (
    "read_current_article",
    "get_current_selection",
    "preview_current_article_edit",
)


def create_editor_agent_plan_tools(runtime: Any) -> list[Any]:
    return [
        create_read_current_article_tool(runtime),
        create_get_current_selection_tool(runtime),
        create_preview_current_article_edit_tool(runtime),
    ]
