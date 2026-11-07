"""Read and rewrite Markdown destinations using original UTF-8 byte spans."""

from dataclasses import dataclass
import html
from pathlib import PurePosixPath
import posixpath
import re
import string
from urllib.parse import quote, unquote

from tree_sitter import Language, Parser, Range
import tree_sitter_markdown

BLOCK = Language(tree_sitter_markdown.language())
INLINE = Language(tree_sitter_markdown.inline_language())
ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
ENTITY = re.compile(r"&(?:#[xX][a-fA-F0-9]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);")
DESTINATION_TOKEN = re.compile(ESCAPE.pattern + "|" + ENTITY.pattern + r"|[?#]")
BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
SCHEME = re.compile(r"^[a-z][a-z\d+.-]*:", re.IGNORECASE)


@dataclass(frozen=True)
class Destination:
    start: int
    end: int
    value: str
    path_end: int


def body_offset(raw):
    start = len(b"\xef\xbb\xbf") if raw.startswith(b"\xef\xbb\xbf") else 0
    lines = raw[start:].splitlines(keepends=True)
    if lines and lines[0].strip() == b"---":
        offset = start + len(lines[0])
        for line in lines[1:]:
            offset += len(line)
            if line.strip() == b"---":
                return offset
    return start


def descendants(root):
    pending = [root]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(reversed(node.named_children))


def destination_at(node, offset):
    start, end = node.start_byte + offset, node.end_byte + offset
    value = node.text.decode("utf-8")
    if value.startswith("<") and value.endswith(">"):
        start, end, value = start + 1, end - 1, value[1:-1]
    suffix_start = None

    def decode(match):
        nonlocal suffix_start
        decoded = match[1] if match[1] is not None else html.unescape(match[0])
        if suffix_start is None and ("?" in decoded or "#" in decoded):
            suffix_start = match.start()
        return decoded

    decoded = DESTINATION_TOKEN.sub(decode, value)
    path_end = end if suffix_start is None else start + len(value[:suffix_start].encode("utf-8"))
    return Destination(start, end, decoded, path_end)


def inline_ranges(node):
    start_point, start_byte = node.start_point, node.start_byte
    for child in node.named_children:
        if child.type == "block_continuation":
            yield Range(start_point, child.start_point, start_byte, child.start_byte)
            start_point, start_byte = child.end_point, child.end_byte
    if start_byte < node.end_byte:
        yield Range(start_point, node.end_point, start_byte, node.end_byte)


def destinations(raw):
    offset = body_offset(raw)
    body = raw[offset:]
    block = Parser(BLOCK).parse(body)
    inline_parser = Parser(INLINE)
    for node in descendants(block.root_node):
        if node.type == "inline":
            # Parse around quote and list prefixes without losing original offsets.
            inline_parser.included_ranges = list(inline_ranges(node))
            inline = inline_parser.parse(body)
            for child in descendants(inline.root_node):
                if child.type == "link_destination":
                    yield destination_at(child, offset)
        elif node.type == "link_reference_definition":
            for child in node.named_children:
                if child.type == "link_destination":
                    yield destination_at(child, offset)


def rewrite_destinations(raw, replace_path):
    """Replace destination paths while leaving original query and fragment bytes intact."""
    chunks = []
    end = 0
    for destination in destinations(raw):
        updated = replace_path(destination.value)
        if updated is not None:
            chunks.extend((raw[end:destination.start], updated.encode("utf-8")))
            end = destination.path_end
    return b"".join((*chunks, raw[end:]))


def split_reference(value):
    match = re.search(r"[?#]", value)
    return (value[:match.start()], value[match.start():]) if match else (value, "")


def decoded_parts(path):
    parts = []
    if BAD_PERCENT.search(path):
        return None
    try:
        for part in path.split("/"):
            decoded = unquote(part, errors="strict")
            if any(character in decoded for character in ("/", "\\", "\0")):
                return None
            parts.append(decoded)
    except UnicodeError:
        return None
    return parts


def resolve_reference(document, value):
    """Resolve a Markdown-relative destination, retaining its query/fragment."""
    path, suffix = split_reference(value)
    if not path or path.startswith("/") or SCHEME.match(path):
        return None
    parts = decoded_parts(path)
    if parts is None:
        return None
    resolved = document.split("/")[:-1]
    for part in parts:
        if part == "..":
            if not resolved:
                return None
            resolved.pop()
        elif part and part != ".":
            resolved.append(part)
    return ("/".join(resolved), suffix) if resolved else None


def relative_reference(document, target):
    parent = str(PurePosixPath(document).parent)
    path = posixpath.relpath(target, parent)
    encoded = "".join(character if not character.isascii() and not character.isspace() else quote(character, safe="/") for character in path)
    return encoded if encoded.startswith("../") else "./" + encoded


def category_route(path):
    return "/" + re.sub(r"\.(md|mdx)$", "", path, flags=re.IGNORECASE)


def document_route(path):
    target = PurePosixPath(path)
    if target.name.lower() == "readme.md":
        return category_route("" if target.parent == PurePosixPath(".") else str(target.parent))
    return category_route(path)


def route_reference(path):
    return "/".join(quote(part) for part in path.split("/"))
