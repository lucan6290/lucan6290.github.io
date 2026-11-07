"""Read and patch the article form without reserializing the YAML document."""

import json
import re

from tree_sitter import Parser
import yaml

from article_frontmatter import ArticleError, references
from content_store import ContentError, first_heading, parse_markdown
from markdown_links import BLOCK, body_offset, descendants

FORM_FIELDS = ("title", "description", "tags", "sticky")
LINE_BREAK = re.compile(r"(?:\r\n|\r|\n)[ \t]*\Z")


def read_header(raw):
    try:
        metadata, body = parse_markdown(raw)
    except ContentError as error:
        raise ArticleError(error.message) from error
    clean = raw.removeprefix("\ufeff")
    lines = clean.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---" or any(name not in metadata for name in FORM_FIELDS):
        raise ArticleError("表单需要已有 title、description、tags、sticky；可在源码中补齐")
    closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    header = "".join(lines[1:closing])
    offset = len(raw) - len(clean) + len(lines[0])
    return metadata, body, header, offset


def form_fields(raw):
    metadata, _, _, _ = read_header(raw)
    values = {name: metadata[name] for name in FORM_FIELDS}
    if (not isinstance(values["title"], str) or not isinstance(values["description"], str)
            or not isinstance(values["tags"], list) or any(not isinstance(tag, str) for tag in values["tags"])
            or type(values["sticky"]) is not bool):
        raise ArticleError("表单字段类型不符合文章约定，请在源码中修复")
    return values


def field_replacement(header, document, tokens, key, node, value):
    if node.start_mark.index < key.end_mark.index or any(
        references(other, node, set()) for pair in document.value if pair[0] is not key for other in pair
    ):
        raise ArticleError(f"{key.value} 使用了共享 YAML 值，请在源码中修改")
    start, end = node.start_mark.index, node.end_mark.index
    selected = [token for token in tokens
                if start <= token.start_mark.index < end and token.end_mark.index <= end]
    first_value = next((token for token in selected if not isinstance(token, (yaml.AnchorToken, yaml.TagToken))), None)
    if first_value is not None:
        start = first_value.start_mark.index
    replacement = json.dumps(value, ensure_ascii=False)
    comments, cursor = [], start
    for token in selected:
        if token.start_mark.index >= cursor:
            comments.extend(re.findall(r"#[^\r\n]*", header[cursor:token.start_mark.index]))
            cursor = token.end_mark.index
    comments.extend(re.findall(r"#[^\r\n]*", header[cursor:end]))
    newline = "\r\n" if "\r\n" in header else "\n"
    if comments:
        replacement += "".join(newline + " " * key.start_mark.column + comment for comment in comments)
    trailing = LINE_BREAK.search(header[start:end])
    if trailing:
        replacement += trailing[0]
    return start, end, replacement


def set_body_title(raw, title):
    data = raw.encode("utf-8")
    offset = body_offset(data)
    body = data[offset:]
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    for node in descendants(Parser(BLOCK).parse(body).root_node):
        if node.type == "setext_heading" and any(child.type == "setext_h1_underline" for child in node.named_children):
            line_start = body.rfind(b"\n", 0, node.start_byte) + 1
            leading = body[line_start:node.start_byte]
            if len(leading) <= 3 and not leading.strip(b" "):
                result = body[:node.start_byte] + b"# " + title.encode("utf-8") + newline + body[node.end_byte:]
                return (data[:offset] + result).decode("utf-8")
        if node.type != "atx_heading":
            continue
        marker = next((child for child in node.named_children if child.type == "atx_h1_marker"), None)
        if marker is None:
            continue
        line_start = body.rfind(b"\n", 0, marker.start_byte) + 1
        leading = body[line_start:marker.start_byte]
        if len(leading) > 3 or leading.strip(b" "):
            continue
        heading = node.child_by_field_name("heading_content")
        if heading:
            closing = re.search(rb"[ \t]+#+[ \t]*\Z", heading.text)
            heading_end = heading.start_byte + closing.start() if closing else heading.end_byte
            result = body[:heading.start_byte] + title.encode("utf-8") + body[heading_end:]
        else:
            end = marker.end_byte
            while body[end:end + 1] in {b" ", b"\t"}:
                end += 1
            result = body[:marker.end_byte] + b" " + title.encode("utf-8") + body[end:]
        return (data[:offset] + result).decode("utf-8")
    return (data[:offset] + newline + b"# " + title.encode("utf-8") + newline * 2 + body).decode("utf-8")


def patch_fields(raw, changes):
    original = form_fields(raw)
    changed = {key: value for key, value in changes.items() if original[key] != value}
    if not changed:
        return raw
    if "title" in changed and (not changed["title"].strip() or "\r" in changed["title"] or "\n" in changed["title"]):
        raise ArticleError("标题必须是非空单行文字")
    if "tags" in changed and (any(not tag.strip() for tag in changed["tags"])
                              or len(set(changed["tags"])) != len(changed["tags"])):
        raise ArticleError("标签不能为空或重复")

    _, _, header, offset = read_header(raw)
    document = yaml.compose(header, Loader=yaml.SafeLoader)
    entries = {key.value: (key, value) for key, value in document.value if isinstance(key, yaml.ScalarNode)}
    if len(entries) != len(document.value) or any(name not in entries for name in changed):
        raise ArticleError("表单字段必须是独立的根级键，请在源码中修改")
    tokens = list(yaml.scan(header, Loader=yaml.SafeLoader))
    replacements = [
        field_replacement(header, document, tokens, *entries[name], value) for name, value in changed.items()
    ]
    result = raw
    for start, end, replacement in sorted(replacements, reverse=True):
        result = result[:offset + start] + replacement + result[offset + end:]
    if "title" in changed:
        result = set_body_title(result, changed["title"])
    metadata, body = parse_markdown(result)
    if any(metadata.get(key) != value for key, value in changed.items()):
        raise ArticleError("表单无法安全修改该 YAML，请改用源码编辑")
    if "title" in changed and first_heading(body) != changed["title"]:
        raise ArticleError("该标题不能原样放入 Markdown 一级标题，请在源码中调整")
    return result
