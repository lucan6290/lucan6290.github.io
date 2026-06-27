"""Simple deterministic retrieval for local knowledge QA."""
from __future__ import annotations

import re
from typing import Any

from .schemas import KnowledgeCitation


def classify_question(question: str) -> str:
    q = question.strip().lower()
    if any(word in q for word in ["有哪些文章", "多少篇", "一共", "文章清单", "所有文章"]):
        return "inventory"
    if any(word in q for word in ["草稿", "分类", "标签", "最近", "更新"]):
        return "metadata"
    if any(word in q for word in ["总结", "关注", "方向", "归纳"]):
        return "summary"
    if any(word in q for word in ["讲了什么", "有没有写过", "在哪篇", "记录过", "内容"]):
        return "content"
    return "content"


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]{2,}", text.lower())
    return [word for word in words if len(word.strip()) >= 2]


def retrieve_articles(question: str, articles: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    terms = tokenize(question)
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in articles:
        haystacks = {
            "title": str(item.get("title", "")).lower(),
            "file": str(item.get("fileName", "")).lower(),
            "tags": " ".join(item.get("tags", [])).lower(),
            "category": " ".join("/".join(cat) for cat in item.get("categories", [])).lower(),
            "description": str(item.get("description", "")).lower(),
            "excerpt": str(item.get("excerpt", "")).lower(),
        }
        score = 0
        for term in terms:
            if term in haystacks["title"]:
                score += 8
            if term in haystacks["file"]:
                score += 6
            if term in haystacks["tags"]:
                score += 6
            if term in haystacks["category"]:
                score += 4
            if term in haystacks["description"]:
                score += 3
            if term in haystacks["excerpt"]:
                score += 1
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _score, item in scored[:limit]]


def retrieve_chunks(question: str, chunks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    terms = tokenize(question)
    scored: list[tuple[int, dict[str, Any]]] = []
    for chunk in chunks:
        text = " ".join(chunk.get("headingPath", [])) + "\n" + str(chunk.get("text", ""))
        lowered = text.lower()
        score = sum(3 if term in " ".join(chunk.get("headingPath", [])).lower() else 0 for term in terms)
        score += sum(1 for term in terms if term in lowered)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _score, item in scored[:limit]]


def build_inventory_answer(articles: list[dict[str, Any]], scanned_at: str) -> str:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in articles:
        category = "未分类"
        cats = item.get("categories") or []
        if cats and cats[0]:
            category = cats[0][0]
        groups.setdefault(category, []).append(item)

    lines = [f"当前共扫描到 {len(articles)} 篇文章。", ""]
    for category, items in sorted(groups.items()):
        lines.append(f"{category}（{len(items)} 篇）")
        for item in sorted(items, key=lambda x: str(x.get("date", "")), reverse=True):
            sub = ""
            cats = item.get("categories") or []
            if cats and len(cats[0]) > 1:
                sub = cats[0][1]
            status = item.get("status") or "unknown"
            lines.append(f"- {item.get('title')}｜二级：{sub or '未填写'}｜状态：{status}｜{item.get('path')}")
        lines.append("")
    lines.append(f"扫描时间：{scanned_at}")
    return "\n".join(lines).strip()


def citations_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        key = (str(chunk.get("articlePath")), "/".join(chunk.get("headingPath", [])))
        if key in seen:
            continue
        seen.add(key)
        line_range = None
        if chunk.get("startLine") and chunk.get("endLine"):
            line_range = [chunk["startLine"], chunk["endLine"]]
        citations.append(KnowledgeCitation(
            title=str(chunk.get("articleTitle")),
            path=str(chunk.get("articlePath")),
            headingPath=list(chunk.get("headingPath", [])),
            lines=line_range,
        ).model_dump())
    return citations
