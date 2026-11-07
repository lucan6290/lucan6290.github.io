import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from content_moves import ContentMoves
from content_store import ContentError, ContentStore


class ContentMoveTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.content = Path(tmp.name) / "frontend/content"
        (self.content / "blog/来源").mkdir(parents=True)
        (self.content / "blog/目标").mkdir()
        self.store = ContentStore(Path(tmp.name))
        self.moves = ContentMoves(self.store)
        self.source = "blog/来源/文章 一.md"
        self.target = "blog/目标/改名 (一).md"
        self.other = "blog/另文.md"
        self.old_article = ("\ufeff---\r\ntitle: 文章 # 保留\r\n---\r\n"
                            "# 文章\r\n\r\n![图](<./文章 一-images/截图 (1).png>)\r\n"
                            "[来源](./README.md?q=1#原目录)\r\n\r\n").encode()
        self.old_other = ("[文章](<./来源/文章 一.md?q=1#标题> \"保留标题\")\n\n"
                          "[URL](/blog/来源/文章%20一?x=1#标题)\n\n"
                          "[图片][图]\n\n[图]: <./来源/文章 一-images/截图 (1).png>\n\n"
                          "\x60[代码](<./来源/文章 一.md>)\x60\n").encode()
        self.write(self.source, self.old_article)
        self.write(self.other, self.old_other)
        self.write("blog/来源/README.md", b"# Intro")
        self.image = "blog/来源/文章 一-images/截图 (1).png"
        self.write(self.image, b"asset bytes")

    def write(self, path, data):
        target = self.content / path
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_bytes(data)

    def plan(self, source=None, target=None, kind="document"):
        return self.moves.plan(source or self.source, target or self.target, kind)

    def test_document_move_previews_and_repairs_links_and_media(self):
        plan = self.plan()
        self.assertEqual(plan["routes"], [{"before": "/blog/来源/文章 一", "after": "/blog/目标/改名 (一)"}])
        self.assertIn({"before": self.other, "after": self.other, "rewritten": True}, plan["files"])
        self.assertIn({"before": self.image, "after": "blog/目标/改名 (一)-images/截图 (1).png", "rewritten": False},
                      plan["files"])
        self.assertTrue((self.content / self.source).is_file())
        self.moves.apply(self.source, self.target, "document", plan["plan_id"])
        self.assertFalse((self.content / self.source).exists())
        self.assertEqual((self.content / "blog/目标/改名 (一)-images/截图 (1).png").read_bytes(), b"asset bytes")
        moved = (self.content / self.target).read_bytes()
        self.assertIn(b"\xef\xbb\xbf---\r\n", moved)
        self.assertIn("./改名%20%28一%29-images/截图%20%281%29.png".encode(), moved)
        self.assertIn("../来源/README.md?q=1#原目录".encode(), moved)
        inbound = (self.content / self.other).read_text(encoding="utf-8")
        self.assertIn('./目标/改名%20%28一%29.md?q=1#标题> "保留标题"', inbound)
        self.assertIn("/blog/%E7%9B%AE%E6%A0%87/%E6%94%B9%E5%90%8D%20%28%E4%B8%80%29?x=1#标题", inbound)
        self.assertIn("[图]: <./目标/改名%20%28一%29-images/截图%20%281%29.png>", inbound)
        self.assertIn("\x60[代码](<./来源/文章 一.md>)\x60", inbound)

    def test_directory_move_changes_routes_and_leaves_internal_relative_links(self):
        source, target = "blog/来源", "blog/目标/新名字"
        plan = self.plan(source, target, "directory")
        self.assertIn({"before": "/blog/来源", "after": "/blog/目标/新名字"}, plan["routes"])
        self.moves.apply(source, target, "directory", plan["plan_id"])
        self.assertEqual((self.content / "blog/目标/新名字/文章 一.md").read_bytes(), self.old_article)
        self.assertIn("./目标/新名字/文章%20一.md".encode(), (self.content / self.other).read_bytes())

    def test_name_collision_and_stale_external_changes_leave_originals(self):
        plan = self.plan()
        self.write(self.other, self.old_other + b"\nexternal")
        with self.assertRaises(ContentError) as conflict:
            self.moves.apply(self.source, self.target, "document", plan["plan_id"])
        self.assertEqual(conflict.exception.status, 409)
        self.assertEqual((self.content / self.source).read_bytes(), self.old_article)
        self.assertFalse((self.content / self.target).exists())
        self.write(self.target, b"# Occupied")
        with self.assertRaises(ContentError) as collision:
            self.plan()
        self.assertEqual(collision.exception.status, 409)
        self.assertEqual((self.content / self.target).read_bytes(), b"# Occupied")

    def test_replacement_failure_rolls_back_prior_rewrites_and_moves(self):
        plan = self.plan()
        real_replace = os.replace
        failed = False

        def replace(source, destination):
            nonlocal failed
            if Path(destination) == self.content / self.target and not failed:
                failed = True
                raise OSError("simulated filesystem failure")
            return real_replace(source, destination)

        with patch("content_moves.os.replace", side_effect=replace), self.assertRaises(ContentError) as failure:
            self.moves.apply(self.source, self.target, "document", plan["plan_id"])
        self.assertEqual(failure.exception.code, "move_failed")
        self.assertTrue(failed)
        self.assertEqual((self.content / self.source).read_bytes(), self.old_article)
        self.assertEqual((self.content / self.other).read_bytes(), self.old_other)
        self.assertEqual((self.content / self.image).read_bytes(), b"asset bytes")
        self.assertFalse((self.content / self.target).exists())
        self.assertFalse(list(self.content.rglob(".desktop-*")))

    def test_markdown_graph_uses_current_file_and_absolute_routes(self):
        graph = self.moves.graph()
        self.assertIn({"source": self.other, "target": self.source}, graph["edges"])
        self.assertIn({"source": self.source, "target": "blog/来源/README.md"}, graph["edges"])
        self.assertEqual(sum(edge["source"] == self.other for edge in graph["edges"]), 1)
