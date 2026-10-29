"""校验文章元信息，并精确维护 updated 值而不重写 YAML。"""
from datetime import datetime, timedelta, timezone
import re

import yaml

FIELDS = ("title", "date", "updated", "description", "tags", "sticky")
LEGACY_FIELDS = {"authors", "slug", "sidebar_position", "created", "createdAt"}
BEIJING = timezone(timedelta(hours=8))
DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00\Z")


class ArticleError(ValueError):
    pass


def exempt(filename):
    return filename.lower() in {"readme.md", "agents.md"}


def references(node, target, visited):
    if node is target:
        return True
    if id(node) in visited:
        return False
    visited.add(id(node))
    if isinstance(node, yaml.MappingNode):
        return any(references(child, target, visited) for pair in node.value for child in pair)
    if isinstance(node, yaml.SequenceNode):
        return any(references(child, target, visited) for child in node.value)
    return False


def nodes(raw):
    lines = raw.removeprefix("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ArticleError("普通文章必须填写六字段 Front Matter")
    closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    document = yaml.compose("".join(lines[1:closing]), Loader=yaml.SafeLoader)
    if not isinstance(document, yaml.MappingNode):
        raise ArticleError("普通文章必须填写六字段 Front Matter")
    result = {}
    for key, value in document.value:
        if key.value in result:
            raise ArticleError(f"Front Matter 不允许重复字段：{key.value}")
        if key.value == "updated" and value.start_mark.index < key.end_mark.index:
            raise ArticleError("updated 必须使用独立时间字符串，不能引用其他字段的 YAML 别名")
        result[key.value] = value
    updated = result.get("updated")
    if updated is not None and any(references(child, updated, set())
                                   for key, value in document.value if key.value != "updated"
                                   for child in (key, value)):
        raise ArticleError("updated 不允许被 date 或其他元信息通过 YAML 别名引用，请改为独立值")
    return result, len(raw) - len(raw.removeprefix("\ufeff")) + len(lines[0])


def timestamp(value, field):
    if not isinstance(value, str) or not DATE_FORMAT.fullmatch(value):
        raise ArticleError(f"{field} 必须是 YYYY-MM-DDTHH:mm:ss+08:00 时间字符串")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ArticleError(f"{field} 不是有效时间，请确认真实写作时间") from error


def validate(raw, metadata, body_heading, *, creating=False):
    values, _ = nodes(raw)
    if any(field not in metadata for field in FIELDS):
        raise ArticleError("普通文章必须保留 title、date、updated、description、tags、sticky 六字段")
    if "updated" not in values:
        raise ArticleError("updated 必须是根级独立字段，不能仅通过 YAML 合并继承，请确认并填写独立时间字符串")
    for field in ("title", "description"):
        if not isinstance(metadata[field], str) or not metadata[field].strip():
            raise ArticleError(f"{field} 必须是非空字符串")
    if metadata["title"] != body_heading:
        raise ArticleError("title 必须与正文首个一级标题一致")
    date = timestamp(metadata["date"], "date")
    updated = timestamp(metadata["updated"], "updated")
    if updated < date:
        raise ArticleError("updated 不得早于 date")
    tags = metadata["tags"]
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise ArticleError("tags 必须是非空字符串组成的数组，无标签时使用 []")
    if len(tags) != len(set(tags)):
        raise ArticleError("tags 不允许重复标签")
    if type(metadata["sticky"]) is not bool:
        raise ArticleError("sticky 必须是布尔值")
    if creating:
        if list(values)[:len(FIELDS)] != list(FIELDS):
            raise ArticleError("六字段必须按 title、date、updated、description、tags、sticky 顺序位于头部")
        if LEGACY_FIELDS.intersection(metadata):
            raise ArticleError("新文章不允许 authors、slug、sidebar_position、created、createdAt 字段")
        if date != updated:
            raise ArticleError("新文章的 date 与 updated 必须相同")
        for field in ("title", "date", "updated", "description"):
            node = values[field]
            if not isinstance(node, yaml.ScalarNode) or node.style != '"':
                raise ArticleError(f"{field} 必须使用双引号字符串")
        tag_node = values["tags"]
        if (not isinstance(tag_node, yaml.SequenceNode) or not tag_node.flow_style
                or any(not isinstance(tag, yaml.ScalarNode) or tag.style != '"'
                       or tag.start_mark.index < tag_node.start_mark.index for tag in tag_node.value)
                or tag_node.start_mark.line != tag_node.end_mark.line):
            raise ArticleError("tags 必须使用双引号字符串的行内数组")
        if values["sticky"].value not in {"true", "false"}:
            raise ArticleError("sticky 必须使用 true 或 false")


def replace_updated(raw, replacement):
    values, offset = nodes(raw)
    if "updated" not in values:
        raise ArticleError("updated 必须是根级独立字段，请确认并填写独立时间字符串")
    node = values["updated"]
    # ScalarToken 从引号/值起算，避免 MappingNode 的范围包含 &anchor。
    token = next(token for token in yaml.scan(raw[offset:], Loader=yaml.SafeLoader)
                 if isinstance(token, yaml.ScalarToken) and token.end_mark.index == node.end_mark.index)
    return raw[:offset + token.start_mark.index] + replacement + raw[offset + token.end_mark.index:]


def maintain_updated(previous, raw, old_metadata, metadata, body_heading):
    validate(raw, metadata, body_heading)
    if "date" in old_metadata:
        timestamp(old_metadata["date"], "磁盘 date，请先按说明文档用途确认真实历史时间")
        if metadata["date"] != old_metadata["date"]:
            raise ArticleError("date 是首次开始写作时间，创建后不可修改；请保留磁盘中的真实 date")
    normalized = replace_updated(raw, '"__updated__"')
    try:
        old_normalized = replace_updated(previous, '"__updated__"')
    except ArticleError:
        # 当前来稿已经完整校验；旧格式无法定位时允许作者修复为独立字段。
        old_normalized = None
    if old_normalized == normalized:
        return previous
    date = timestamp(metadata["date"], "date")
    current = max(datetime.now(BEIJING).replace(microsecond=0), date).isoformat(timespec="seconds")
    return replace_updated(raw, f'"{current}"')
