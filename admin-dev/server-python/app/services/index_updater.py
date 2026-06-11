"""
index.md 目录自动更新引擎

纯函数式引擎：输入 index.md 文本 + 操作指令 → 输出修改后文本。
所有核心函数均为纯函数，不涉及文件 I/O。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Article:
    """目录中的文章链接行"""
    line: str  # 原始链接行，如 "- [标题](/URL/)"


@dataclass
class Subcategory:
    """二级分类"""
    number: str          # "1.1"
    title: str           # "AI 探索"
    heading: str         # 原始标题行 "### 1.1 AI 探索"
    articles: list[Article] = field(default_factory=list)


@dataclass
class PrimaryCategory:
    """一级分类"""
    number: str          # "一"
    title: str           # "技术研习"
    heading: str         # 原始标题行 "## 一、技术研习"
    subcategories: list[Subcategory] = field(default_factory=list)
    placeholder: str | None = None  # "*暂无文章，敬请期待*" 或 None


@dataclass
class IndexStructure:
    """index.md 解析后的完整结构"""
    front_matter: str     # front matter 原始文本（含 --- 分隔符）
    categories: list[PrimaryCategory] = field(default_factory=list)
    footer: str = ""      # 末尾 "*持续更新，记录成长*" 等内容
    unknown_lines: list[str] = field(default_factory=list)  # 无法识别的行，原样保留


# ============================================================
# 正则模式
# ============================================================

# 一级分类标题：## 一、技术研习
_RE_PRIMARY = re.compile(r"^##\s+([一二三四五六七八九十]+)、(.+)$")

# 二级分类标题：### 1.1 AI 探索
_RE_SUBCATEGORY = re.compile(r"^###\s+(\d+\.\d+)\s+(.+)$")

# 文章链接行：- [标题](/URL/)
_RE_ARTICLE = re.compile(r"^-\s+\[.*?\]\(/.*?/\)$")

# 占位符
_RE_PLACEHOLDER = re.compile(r"^\*暂无文章，敬请期待\*$")


# ============================================================
# 解析器
# ============================================================

def parse_index(index_text: str) -> IndexStructure:
    """
    解析 index.md 文本为 IndexStructure。

    Args:
        index_text: index.md 的完整文本

    Returns:
        IndexStructure 解析结果

    Raises:
        ValueError: index_text 为空或无 front matter
    """
    if not index_text or not index_text.strip():
        raise ValueError("目录文件内容为空，请检查 index.md 格式")

    # 1. 分离 front matter
    text = index_text.lstrip("\n")
    if not text.startswith("---"):
        raise ValueError("index.md Front Matter 格式异常，无法解析")

    # 找到第二个 ---
    end = text.find("---", 3)
    if end == -1:
        raise ValueError("index.md Front Matter 格式异常，无法解析")

    front_matter = text[: end + 3]
    body = text[end + 3:].lstrip("\n")

    structure = IndexStructure(front_matter=front_matter)

    # 2. 逐行解析 body
    lines = body.split("\n")
    current_primary: PrimaryCategory | None = None
    current_sub: Subcategory | None = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # 空行跳过
        if not line.strip():
            i += 1
            continue

        # 一级分类标题
        m = _RE_PRIMARY.match(line)
        if m:
            current_primary = PrimaryCategory(
                number=m.group(1),
                title=m.group(2),
                heading=line,
            )
            structure.categories.append(current_primary)
            current_sub = None
            i += 1
            continue

        # 二级分类标题
        m = _RE_SUBCATEGORY.match(line)
        if m and current_primary is not None:
            current_sub = Subcategory(
                number=m.group(1),
                title=m.group(2),
                heading=line,
            )
            current_primary.subcategories.append(current_sub)
            i += 1
            continue

        # 占位符
        if _RE_PLACEHOLDER.match(line) and current_primary is not None:
            current_primary.placeholder = line
            i += 1
            continue

        # 文章链接
        if _RE_ARTICLE.match(line) and current_sub is not None:
            current_sub.articles.append(Article(line=line))
            i += 1
            continue

        # #### 系列文章组标题 → 收集直到下一个空行或同级标题
        if line.startswith("####") and current_primary is not None:
            series_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                # 遇到空行且下一行是已识别的模式则停止
                if not next_line.strip():
                    # 检查空行后面是什么
                    if j + 1 < len(lines):
                        peek = lines[j + 1]
                        if (_RE_PRIMARY.match(peek)
                                or _RE_SUBCATEGORY.match(peek)
                                or peek.startswith("##")
                                or peek.startswith("---")):
                            break
                    series_lines.append(next_line)
                    j += 1
                    continue
                # 遇到同级或更高级标题
                if (next_line.startswith("###") or next_line.startswith("##")
                        or next_line.startswith("---")):
                    break
                series_lines.append(next_line)
                j += 1
            structure.unknown_lines.extend(series_lines)
            i = j
            continue

        # --- 分隔符（一级分类之间）
        if line.strip() == "---":
            i += 1
            continue

        # footer: *持续更新，记录成长*
        if line.startswith("*持续更新") or line.startswith("* 持续更新"):
            structure.footer = line
            i += 1
            continue

        # 开头的描述文本（如 **📚 箓川码笺文章总目录**）
        if line.startswith("**") and line.endswith("**"):
            structure.unknown_lines.append(line)
            i += 1
            continue

        # 其他无法识别的行
        structure.unknown_lines.append(line)
        i += 1
        continue

    return structure


# ============================================================
# 序列化器
# ============================================================

def serialize(structure: IndexStructure) -> str:
    """
    将 IndexStructure 序列化回 markdown 文本。

    Args:
        structure: 解析后的目录结构

    Returns:
        完整的 index.md 文本
    """
    parts: list[str] = [structure.front_matter]

    # 保留 front matter 后、一级分类前的未知行（如 **📚 ...**）
    pre_category_unknowns: list[str] = []
    remaining_unknowns: list[str] = []
    found_first_category = False
    for ul in structure.unknown_lines:
        if not found_first_category:
            pre_category_unknowns.append(ul)
            # 如果这行看起来是开头的装饰性文本
            if ul.startswith("**") and ul.endswith("**"):
                continue
        else:
            remaining_unknowns.append(ul)

    # 输出开头的未知行
    if pre_category_unknowns:
        parts.append("\n".join(pre_category_unknowns))
        parts.append("")

    # 遍历一级分类
    for idx, cat in enumerate(structure.categories):
        if idx > 0:
            parts.append("")
            parts.append("---")
            parts.append("")

        parts.append(cat.heading)
        parts.append("")

        if cat.subcategories:
            for sub in cat.subcategories:
                parts.append(sub.heading)
                parts.append("")
                for article in sub.articles:
                    parts.append(article.line)
                parts.append("")
        elif cat.placeholder:
            parts.append(cat.placeholder)
            parts.append("")

    # 输出末尾的未知行（系列文章等）
    if remaining_unknowns:
        parts.append("")
        parts.append("\n".join(remaining_unknowns))
        parts.append("")

    # 最后一个一级分类的 ---
    # footer 前
    if structure.footer:
        parts.append("---")
        parts.append("")
        parts.append(structure.footer)

    text = "\n".join(parts)
    # 清理多余空行（超过2个连续空行缩减为1个）
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 确保末尾有换行
    if not text.endswith("\n"):
        text += "\n"

    return text
