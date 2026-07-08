"""Tool: read the current bound article."""

from __future__ import annotations

from typing import Any


def read_current_article(article: Any) -> dict[str, Any]:
    # version 是当前文章内容 hash，后续写入会用它做乐观锁校验。
    return {
        "article": {
            "id": article.id,
            "title": article.title,
            "frontmatter": article.frontmatter,
            "body": article.body,
            "version": article.version,
        }
    }


def create_read_current_article_tool(runtime: Any) -> Any:
    from langchain.tools import tool

    def _run() -> dict[str, Any]:
        """读取当前绑定文章的 frontmatter、正文和版本号。"""
        return runtime.read_current_article()

    return tool(
        "read_current_article",
        description="读取当前绑定文章的 frontmatter、正文和版本号。",
    )(_run)
