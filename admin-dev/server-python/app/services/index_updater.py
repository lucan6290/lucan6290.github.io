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
# 中文序号映射
# ============================================================

_CHINESE_NUMBERS = [
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
    "十一", "十二", "十三", "十四", "十五",
]


def number_to_chinese(n: int) -> str:
    """数字 → 中文序号（1→一, 2→二, ...），超过映射表动态生成"""
    if 1 <= n <= len(_CHINESE_NUMBERS):
        return _CHINESE_NUMBERS[n - 1]
    # 超出映射表，返回数字字符串
    return str(n)


def chinese_to_number(chinese: str) -> int:
    """中文序号 → 数字（一→1, 二→2, ...）"""
    if chinese in _CHINESE_NUMBERS:
        return _CHINESE_NUMBERS.index(chinese) + 1
    return 0


# ============================================================
# 链接生成
# ============================================================

def generate_link_line(date: str, category_slug: str, filename: str, title: str) -> str:
    """
    生成目录链接行。

    Args:
        date: 文章日期，如 "2026-06-08 15:30:00" 或 "2026-06-08"
        category_slug: 分类 slug，如 "tech-study"
        filename: 文件名（不含 .md），如 "ts-ai-agent入门笔记"
        title: 文章标题

    Returns:
        链接行，如 "- [Agent 入门笔记](/2026/06/08/tech-study/ts-ai-agent入门笔记/)"
    """
    # 提取日期部分
    date_part = date.split(" ")[0]  # "2026-06-08"
    parts = date_part.split("-")
    if len(parts) != 3:
        raise ValueError(f"文章日期格式异常：{date}，无法生成链接")
    year, month, day = parts
    return f"- [{title}](/{year}/{month}/{day}/{category_slug}/{filename}/)"


# ============================================================
# 链接匹配
# ============================================================

def match_link_by_filename(text: str, filename: str) -> Optional[re.Match]:
    """用文件名匹配目录中的链接"""
    pattern = re.compile(rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$", re.MULTILINE)
    return pattern.search(text)


def count_links_by_filename(text: str, filename: str) -> int:
    """统计文件名匹配到的链接数（用于检测重复）"""
    pattern = re.compile(rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$", re.MULTILINE)
    return len(pattern.findall(text))


# ============================================================
# 分类名匹配
# ============================================================

def find_primary_category(
    structure: IndexStructure, category_name: str
) -> Optional[PrimaryCategory]:
    """用中文分类名匹配一级分类（contains 匹配）"""
    for cat in structure.categories:
        if category_name in cat.title or cat.title in category_name:
            return cat
    return None


def find_subcategory(
    primary: PrimaryCategory, sub_name: str
) -> Optional[Subcategory]:
    """匹配二级分类（contains 匹配）"""
    for sub in primary.subcategories:
        if sub_name in sub.title or sub.title in sub_name:
            return sub
    return None


# ============================================================
# 编号工具
# ============================================================

def get_next_chinese_number(structure: IndexStructure) -> str:
    """获取下一个一级分类中文序号"""
    n = len(structure.categories) + 1
    return number_to_chinese(n)


def get_next_sub_number(primary: PrimaryCategory) -> str:
    """获取下一个二级分类编号（如当前最大 1.3 → 返回 1.4）"""
    if not primary.subcategories:
        # 从一级分类编号提取前缀
        primary_num = chinese_to_number(primary.number)
        return f"{primary_num}.1"
    last = primary.subcategories[-1]
    # 解析 "1.3" → prefix="1", suffix=3
    parts = last.number.split(".")
    prefix = parts[0]
    suffix = int(parts[1]) + 1
    return f"{prefix}.{suffix}"


def renumber_subcategories(primary: PrimaryCategory) -> None:
    """重新编号二级分类（消除间隙，如 1.1, 1.3 → 1.1, 1.2）"""
    primary_num = chinese_to_number(primary.number)
    for idx, sub in enumerate(primary.subcategories, start=1):
        new_number = f"{primary_num}.{idx}"
        sub.number = new_number
        sub.heading = f"### {new_number} {sub.title}"


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


# ============================================================
# 核心操作：add_to_index
# ============================================================

def add_to_index(
    index_text: str,
    title: str,
    date: str,
    categories: list[str],
    filename: str,
    category_slug: str,
) -> tuple[str, str]:
    """
    插入文章链接到目录。

    Args:
        index_text: index.md 完整文本
        title: 文章标题
        date: 文章日期
        categories: 分类列表 ["一级分类", "二级分类"]
        filename: 文件名（不含 .md）
        category_slug: 分类 slug

    Returns:
        (new_index_text, message)
    """
    # 校验 categories
    if not categories:
        raise ValueError("文章缺少 categories 字段，无法确定分类位置")

    # 校验 date
    date_part = date.split(" ")[0] if date else ""
    if not date_part or len(date_part.split("-")) != 3:
        raise ValueError(f"文章日期格式异常：{date}，无法生成链接")

    structure = parse_index(index_text)

    # 幂等性：已存在则静默跳过
    if match_link_by_filename(serialize(structure), filename):
        return index_text, f"文章 [{filename}] 已在目录中，跳过插入"

    # 确定分类名
    primary_name = categories[0]
    sub_name = categories[1] if len(categories) > 1 else primary_name

    # 匹配一级分类
    primary = find_primary_category(structure, primary_name)

    if primary is None:
        # 自动追加新一级分类（spec 5.3）
        next_num = get_next_chinese_number(structure)
        heading = f"## {next_num}、{primary_name}"
        primary = PrimaryCategory(
            number=next_num,
            title=primary_name,
            heading=heading,
            placeholder="*暂无文章，敬请期待*",
        )
        structure.categories.append(primary)

    # 匹配二级分类
    sub = find_subcategory(primary, sub_name)

    if sub is None:
        # 自动创建新二级分类
        next_sub_num = get_next_sub_number(primary)
        sub_heading = f"### {next_sub_num} {sub_name}"
        sub = Subcategory(
            number=next_sub_num,
            title=sub_name,
            heading=sub_heading,
        )
        primary.subcategories.append(sub)

    # 清除 placeholder
    primary.placeholder = None

    # 生成链接并追加
    link_line = generate_link_line(date, category_slug, filename, title)
    sub.articles.append(Article(line=link_line))

    new_text = serialize(structure)
    return new_text, f"已将文章 [{title}] 添加到目录"


# ============================================================
# 核心操作：remove_from_index
# ============================================================

def remove_from_index(
    index_text: str,
    filename: str,
) -> tuple[str, str]:
    """
    从目录移除文章链接。

    Args:
        index_text: index.md 完整文本
        filename: 文件名（不含 .md）

    Returns:
        (new_index_text, message)
    """
    structure = parse_index(index_text)

    # 检查重复
    serialized = serialize(structure)
    link_count = count_links_by_filename(serialized, filename)

    if link_count > 1:
        raise ValueError(f"目录中发现重复文件名 [{filename}]，请手动检查 index.md")

    if link_count == 0:
        # 静默跳过
        return index_text, f"未在目录中找到文章 [{filename}] 的链接"

    # 遍历找到并移除
    target_primary: PrimaryCategory | None = None
    target_sub: Subcategory | None = None

    for primary in structure.categories:
        for sub in primary.subcategories:
            for article in sub.articles:
                # 用文件名匹配
                m = re.search(
                    rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$",
                    article.line,
                )
                if m:
                    sub.articles.remove(article)
                    target_primary = primary
                    target_sub = sub
                    break
            if target_sub:
                break
        if target_primary:
            break

    # 二级分类清空 → 移除该二级分类
    if target_sub and not target_sub.articles:
        target_primary.subcategories.remove(target_sub)
        # 重新编号
        renumber_subcategories(target_primary)

    # 一级分类所有二级为空 → 恢复占位符
    if target_primary and not target_primary.subcategories:
        target_primary.placeholder = "*暂无文章，敬请期待*"

    new_text = serialize(structure)
    return new_text, f"已从目录移除文章 [{filename}]"


# ============================================================
# 核心操作：update_in_index
# ============================================================

def update_in_index(
    index_text: str,
    old_filename: str,
    new_title: str,
    new_date: str,
    new_categories: list[str],
    new_filename: str,
    new_category_slug: str,
) -> tuple[str, str]:
    """
    更新目录中的文章链接。

    Args:
        index_text: index.md 完整文本
        old_filename: 旧文件名
        new_title: 新标题
        new_date: 新日期
        new_categories: 新分类列表
        new_filename: 新文件名
        new_category_slug: 新分类 slug

    Returns:
        (new_index_text, message)
    """
    # 校验 categories
    if not new_categories:
        raise ValueError("文章缺少 categories 字段，无法确定分类位置")

    structure = parse_index(index_text)

    # 找到旧链接
    old_primary: PrimaryCategory | None = None
    old_sub: Subcategory | None = None
    old_article: Article | None = None

    for primary in structure.categories:
        for sub in primary.subcategories:
            for article in sub.articles:
                m = re.search(
                    rf"/{re.escape(old_filename)}/\)$",
                    article.line,
                )
                if m:
                    old_primary = primary
                    old_sub = sub
                    old_article = article
                    break
            if old_article:
                break
        if old_article:
            break

    if old_article is None:
        return index_text, f"未在目录中找到文章 [{old_filename}] 的链接"

    # 判断是否分类变更
    old_cat_name = old_primary.title if old_primary else ""
    old_sub_name = old_sub.title if old_sub else ""
    new_cat_name = new_categories[0]
    new_sub_name = new_categories[1] if len(new_categories) > 1 else new_cat_name

    category_changed = (old_cat_name != new_cat_name) or (old_sub_name != new_sub_name)
    filename_changed = old_filename != new_filename

    if category_changed or filename_changed:
        # 分类变更 → remove(旧) + add(新)
        text_after_remove, _ = remove_from_index(index_text, old_filename)
        return add_to_index(
            text_after_remove,
            new_title,
            new_date,
            new_categories,
            new_filename,
            new_category_slug,
        )

    # 只改标题或日期 → 就地更新
    new_link = generate_link_line(new_date, new_category_slug, new_filename, new_title)

    if old_article.line == new_link:
        return index_text, "文章目录信息无变化"

    old_article.line = new_link
    new_text = serialize(structure)
    return new_text, f"已更新目录中文章 [{old_filename}] 的链接"


# ============================================================
# 核心操作：handle_status_change
# ============================================================

def handle_status_change(
    index_text: str,
    title: str,
    date: str,
    categories: list[str],
    filename: str,
    category_slug: str,
    old_status: str,
    new_status: str,
) -> tuple[str, str]:
    """
    根据状态变更决定插入或移除。

    Args:
        index_text: index.md 完整文本
        title: 文章标题
        date: 文章日期
        categories: 分类列表
        filename: 文件名
        category_slug: 分类 slug
        old_status: 旧状态
        new_status: 新状态

    Returns:
        (new_index_text, message)
    """
    was_published = old_status == "published"
    is_published = new_status == "published"

    if not was_published and is_published:
        # 非published → published：插入
        return add_to_index(index_text, title, date, categories, filename, category_slug)

    if was_published and not is_published:
        # published → 非published：移除
        return remove_from_index(index_text, filename)

    # 其他（draft→wip 等）：不处理
    return index_text, f"状态变更 {old_status}→{new_status}，无需更新目录"
