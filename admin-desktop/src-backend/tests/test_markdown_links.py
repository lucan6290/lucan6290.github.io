import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from markdown_links import destinations, relative_reference, resolve_reference, rewrite_destinations


class MarkdownLinkTests(unittest.TestCase):
    def test_source_spans_skip_yaml_inline_code_and_fences(self):
        raw = (
            '\ufeff---\r\ntitle: "[元信息](./no.md)"\r\n---\r\n'
            '> [外链](./中文.md?x=1#锚点)\r\n'
            '![图](<./图 片.png> "标题")\r\n\r\n'
            '[目标]: ../来源.md\r\n\r\n[引用][目标]\r\n'
            '`[代码](./no.md)`\r\n\r\n~~~markdown\r\n[代码](./no.md)\r\n~~~\r\n'
        ).encode("utf-8")
        self.assertEqual(
            [item.value for item in destinations(raw)],
            ["./中文.md?x=1#锚点", "./图 片.png", "../来源.md"],
        )
        updated = rewrite_destinations(raw, lambda value: "./新%20图.png" if value.endswith(".png") else None)
        self.assertEqual(updated, raw.replace("./图 片.png".encode(), "./新%20图.png".encode()))

    def test_relative_resolution_retains_suffix_and_stays_inside_content(self):
        self.assertEqual(resolve_reference("blog/目录/文.md", "../图%20片.png?x=1#锚点"),
                         ("blog/图 片.png", "?x=1#锚点"))
        for invalid in ("../../../../外部.md", "https://example.com/a.md", "/blog/绝对", "./foo%2fbar.md",
                        "./foo%5Cbar.md", "#章节", "./bad%xx.md", "C:/tmp/a.md"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(resolve_reference("blog/目录/文.md", invalid))

    def test_relative_reference_encodes_link_delimiters_and_reserved_chars(self):
        self.assertEqual(relative_reference("blog/文章.md", "blog/文章-images/图 (1)#100%.png"),
                         "./文章-images/图%20%281%29%23100%25.png")
        self.assertEqual(relative_reference("blog/子/文章.md", "blog/README.md"), "../README.md")

