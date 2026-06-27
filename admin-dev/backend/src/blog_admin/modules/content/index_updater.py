from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Article:
    line: str


@dataclass
class Subcategory:
    number: str
    title: str
    heading: str
    articles: list[Article] = field(default_factory=list)
    trailing_lines: list[str] = field(default_factory=list)


@dataclass
class PrimaryCategory:
    number: str
    title: str
    heading: str
    subcategories: list[Subcategory] = field(default_factory=list)
    placeholder: str | None = None


@dataclass
class IndexStructure:
    front_matter: str
    categories: list[PrimaryCategory] = field(default_factory=list)
    footer: str = ""
    unknown_lines: list[str] = field(default_factory=list)


_RE_PRIMARY = re.compile(r"^##\s+([一二三四五六七八九十]+)、(.+)$")
_RE_SUBCATEGORY = re.compile(r"^###\s+(\d+\.\d+)\s+(.+)$")
_RE_ARTICLE = re.compile(r"^-\s+\[.*?\]\(/.*?/\)$")
_RE_PLACEHOLDER = re.compile(r"^\*暂无文章，敬请期待\*$")

_CHINESE_NUMBERS = [
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
    "十",
    "十一",
    "十二",
    "十三",
    "十四",
    "十五",
]


def number_to_chinese(value: int) -> str:
    if 1 <= value <= len(_CHINESE_NUMBERS):
        return _CHINESE_NUMBERS[value - 1]
    return str(value)


def chinese_to_number(chinese: str) -> int:
    if chinese in _CHINESE_NUMBERS:
        return _CHINESE_NUMBERS.index(chinese) + 1
    return 0


def generate_link_line(date: str, category_slug: str, filename: str, title: str) -> str:
    date_part = date.split(" ")[0]
    parts = date_part.split("-")
    if len(parts) != 3:
        raise ValueError(f"文章日期格式异常：{date}，无法生成链接")
    year, month, day = parts
    return f"- [{title}](/{year}/{month}/{day}/{category_slug}/{filename}/)"


def match_link_by_filename(text: str, filename: str) -> re.Match | None:
    pattern = re.compile(rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$", re.MULTILINE)
    return pattern.search(text)


def count_links_by_filename(text: str, filename: str) -> int:
    pattern = re.compile(rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$", re.MULTILINE)
    return len(pattern.findall(text))


def find_primary_category(structure: IndexStructure, category_name: str) -> PrimaryCategory | None:
    for category in structure.categories:
        if category_name in category.title or category.title in category_name:
            return category
    return None


def find_subcategory(primary: PrimaryCategory, sub_name: str) -> Subcategory | None:
    for subcategory in primary.subcategories:
        if sub_name in subcategory.title or subcategory.title in sub_name:
            return subcategory
    return None


def get_next_chinese_number(structure: IndexStructure) -> str:
    return number_to_chinese(len(structure.categories) + 1)


def get_next_sub_number(primary: PrimaryCategory) -> str:
    if not primary.subcategories:
        primary_num = chinese_to_number(primary.number)
        return f"{primary_num}.1"
    last = primary.subcategories[-1]
    prefix, suffix = last.number.split(".")
    return f"{prefix}.{int(suffix) + 1}"


def renumber_subcategories(primary: PrimaryCategory) -> None:
    primary_num = chinese_to_number(primary.number)
    for index, subcategory in enumerate(primary.subcategories, start=1):
        new_number = f"{primary_num}.{index}"
        subcategory.number = new_number
        subcategory.heading = f"### {new_number} {subcategory.title}"


def parse_index(index_text: str) -> IndexStructure:
    if not index_text or not index_text.strip():
        raise ValueError("目录文件内容为空，请检查 index.md 格式")

    text = index_text.lstrip("\n")
    if not text.startswith("---"):
        raise ValueError("index.md Front Matter 格式异常，无法解析")

    end = text.find("---", 3)
    if end == -1:
        raise ValueError("index.md Front Matter 格式异常，无法解析")

    front_matter = text[: end + 3]
    body = text[end + 3 :].lstrip("\n")
    structure = IndexStructure(front_matter=front_matter)

    lines = body.split("\n")
    current_primary: PrimaryCategory | None = None
    current_sub: Subcategory | None = None
    index = 0
    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        primary_match = _RE_PRIMARY.match(line)
        if primary_match:
            current_primary = PrimaryCategory(
                number=primary_match.group(1),
                title=primary_match.group(2),
                heading=line,
            )
            structure.categories.append(current_primary)
            current_sub = None
            index += 1
            continue

        subcategory_match = _RE_SUBCATEGORY.match(line)
        if subcategory_match and current_primary is not None:
            current_sub = Subcategory(
                number=subcategory_match.group(1),
                title=subcategory_match.group(2),
                heading=line,
            )
            current_primary.subcategories.append(current_sub)
            index += 1
            continue

        if _RE_PLACEHOLDER.match(line) and current_primary is not None:
            current_primary.placeholder = line
            index += 1
            continue

        if _RE_ARTICLE.match(line) and current_sub is not None:
            current_sub.articles.append(Article(line=line))
            index += 1
            continue

        if line.startswith("####") and current_primary is not None:
            series_lines = [line]
            cursor = index + 1
            while cursor < len(lines):
                next_line = lines[cursor]
                if not next_line.strip():
                    if cursor + 1 < len(lines):
                        peek = lines[cursor + 1]
                        if (
                            _RE_PRIMARY.match(peek)
                            or _RE_SUBCATEGORY.match(peek)
                            or peek.startswith("##")
                            or peek.startswith("---")
                        ):
                            break
                    series_lines.append(next_line)
                    cursor += 1
                    continue
                if next_line.startswith("###") or next_line.startswith("##") or next_line.startswith("---"):
                    break
                series_lines.append(next_line)
                cursor += 1
            if current_sub is not None:
                current_sub.trailing_lines.extend(series_lines)
            else:
                structure.unknown_lines.extend(series_lines)
            index = cursor
            continue

        if line.strip() == "---":
            index += 1
            continue

        if line.startswith("*持续更新") or line.startswith("* 持续更新"):
            structure.footer = line
            index += 1
            continue

        structure.unknown_lines.append(line)
        index += 1

    return structure


def serialize(structure: IndexStructure) -> str:
    parts: list[str] = [structure.front_matter]

    if structure.unknown_lines:
        parts.append("\n".join(structure.unknown_lines))
        parts.append("")

    for index, category in enumerate(structure.categories):
        if index > 0:
            parts.append("")
            parts.append("---")
            parts.append("")

        parts.append(category.heading)
        parts.append("")

        if category.subcategories:
            for subcategory in category.subcategories:
                parts.append(subcategory.heading)
                parts.append("")
                for article in subcategory.articles:
                    parts.append(article.line)
                if subcategory.trailing_lines:
                    parts.append("")
                    parts.extend(subcategory.trailing_lines)
                parts.append("")
        elif category.placeholder:
            parts.append(category.placeholder)
            parts.append("")

    if structure.footer:
        parts.append("---")
        parts.append("")
        parts.append(structure.footer)

    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text.endswith("\n"):
        text += "\n"
    return text


def add_to_index(
    index_text: str,
    title: str,
    date: str,
    categories: list[str],
    filename: str,
    category_slug: str,
) -> tuple[str, str]:
    if not categories:
        raise ValueError("文章缺少 categories 字段，无法确定分类位置")

    date_part = date.split(" ")[0] if date else ""
    if not date_part or len(date_part.split("-")) != 3:
        raise ValueError(f"文章日期格式异常：{date}，无法生成链接")

    structure = parse_index(index_text)
    if match_link_by_filename(serialize(structure), filename):
        return index_text, f"文章 [{filename}] 已在目录中，跳过插入"

    primary_name = categories[0]
    sub_name = categories[1] if len(categories) > 1 else primary_name
    primary = find_primary_category(structure, primary_name)

    if primary is None:
        next_num = get_next_chinese_number(structure)
        primary = PrimaryCategory(
            number=next_num,
            title=primary_name,
            heading=f"## {next_num}、{primary_name}",
            placeholder="*暂无文章，敬请期待*",
        )
        structure.categories.append(primary)

    subcategory = find_subcategory(primary, sub_name)
    if subcategory is None:
        next_sub_num = get_next_sub_number(primary)
        subcategory = Subcategory(
            number=next_sub_num,
            title=sub_name,
            heading=f"### {next_sub_num} {sub_name}",
        )
        primary.subcategories.append(subcategory)

    primary.placeholder = None
    subcategory.articles.append(Article(line=generate_link_line(date, category_slug, filename, title)))

    return serialize(structure), f"已将文章 [{title}] 添加到目录"


def remove_from_index(index_text: str, filename: str) -> tuple[str, str]:
    structure = parse_index(index_text)
    serialized = serialize(structure)
    link_count = count_links_by_filename(serialized, filename)

    if link_count > 1:
        raise ValueError(f"目录中发现重复文件名 [{filename}]，请手动检查 index.md")
    if link_count == 0:
        return index_text, f"未在目录中找到文章 [{filename}] 的链接"

    target_primary: PrimaryCategory | None = None
    target_sub: Subcategory | None = None

    for primary in structure.categories:
        for subcategory in primary.subcategories:
            for article in list(subcategory.articles):
                if re.search(rf"^-\s+\[.*?\]\(/.*?/{re.escape(filename)}/\)$", article.line):
                    subcategory.articles.remove(article)
                    target_primary = primary
                    target_sub = subcategory
                    break
            if target_sub:
                break
        if target_primary:
            break

    if target_primary and target_sub and not target_sub.articles:
        target_primary.subcategories.remove(target_sub)
        renumber_subcategories(target_primary)

    if target_primary and not target_primary.subcategories:
        target_primary.placeholder = "*暂无文章，敬请期待*"

    return serialize(structure), f"已从目录移除文章 [{filename}]"


def update_in_index(
    index_text: str,
    old_filename: str,
    new_title: str,
    new_date: str,
    new_categories: list[str],
    new_filename: str,
    new_category_slug: str,
) -> tuple[str, str]:
    if not new_categories:
        raise ValueError("文章缺少 categories 字段，无法确定分类位置")

    structure = parse_index(index_text)
    old_primary: PrimaryCategory | None = None
    old_sub: Subcategory | None = None
    old_article: Article | None = None

    for primary in structure.categories:
        for subcategory in primary.subcategories:
            for article in subcategory.articles:
                if re.search(rf"/{re.escape(old_filename)}/\)$", article.line):
                    old_primary = primary
                    old_sub = subcategory
                    old_article = article
                    break
            if old_article:
                break
        if old_article:
            break

    if old_article is None:
        return index_text, f"未在目录中找到文章 [{old_filename}] 的链接"

    old_cat_name = old_primary.title if old_primary else ""
    old_sub_name = old_sub.title if old_sub else ""
    new_cat_name = new_categories[0]
    new_sub_name = new_categories[1] if len(new_categories) > 1 else new_cat_name

    category_changed = (old_cat_name != new_cat_name) or (old_sub_name != new_sub_name)
    filename_changed = old_filename != new_filename
    if category_changed or filename_changed:
        text_after_remove, _ = remove_from_index(index_text, old_filename)
        return add_to_index(
            text_after_remove,
            new_title,
            new_date,
            new_categories,
            new_filename,
            new_category_slug,
        )

    new_link = generate_link_line(new_date, new_category_slug, new_filename, new_title)
    if old_article.line == new_link:
        return index_text, "文章目录信息无变化"

    old_article.line = new_link
    return serialize(structure), f"已更新目录中文章 [{old_filename}] 的链接"


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
    was_published = old_status == "published"
    is_published = new_status == "published"

    if not was_published and is_published:
        return add_to_index(index_text, title, date, categories, filename, category_slug)
    if was_published and not is_published:
        return remove_from_index(index_text, filename)
    return index_text, f"状态变更 {old_status}→{new_status}，无需更新目录"
