"""Runtime context used by editor article tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scr.schemas.agent import EditorAgentRunRequestDTO
from scr.services.ai.tools.editor_operation import normalize_operation, parse_operation_data
from scr.services.ai.tools.get_current_selection import get_current_selection
from scr.services.ai.tools.preview_current_article_edit import preview_current_article_edit
from scr.services.ai.tools.read_current_article import read_current_article


@dataclass
class EditorArticleToolRuntime:
    payload: EditorAgentRunRequestDTO
    article: Any
    last_operation_data: dict[str, Any] | None = None
    last_preview: dict[str, Any] | None = None

    def read_current_article(self) -> dict[str, Any]:
        return read_current_article(self.article)

    def get_current_selection(self) -> dict[str, Any]:
        return get_current_selection(self.payload)

    def preview_current_article_edit(self, operation: dict[str, Any]) -> dict[str, Any]:
        # Agent 的最终方案以预览工具传入的 operation 为准，后续服务层会复用这里缓存的结果。
        self.last_operation_data = operation
        parsed = parse_operation_data(operation)
        parsed = normalize_operation(self.payload, parsed, self.article.body)
        preview = preview_current_article_edit(
            body=self.article.body,
            frontmatter=self.article.frontmatter,
            operation=parsed,
            current_hash=self.article.version,
        )
        self.last_operation_data = parsed.model_dump(by_alias=True)
        self.last_preview = preview
        return {"operation": self.last_operation_data, "preview": preview}
