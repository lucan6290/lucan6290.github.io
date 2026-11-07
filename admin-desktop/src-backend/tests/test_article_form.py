from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from article_form import form_fields, patch_fields
from article_frontmatter import ArticleError
from content_store import parse_markdown


RAW = ("\ufeff---\r\ntitle: '文章' # 保留标题注释\r\n"
       'date: "2026-11-07T10:00:00+08:00"\r\nupdated: "2026-11-07T10:00:00+08:00"\r\n'
       "description: 原摘要\r\ntags: # 组注释\r\n  - 一 # 标签注释\r\n  - 二\r\n"
       "sticky: false # 保留置顶注释\r\nunknown: { nested: [1, 2] } # 保留未知\r\n---\r\n"
       "\r\n~~~markdown\r\n# 代码示例\r\n~~~\r\n\r\n# 文章 ###\r\n\r\n正文\r\n")


class ArticleFormTests(unittest.TestCase):
    def test_patch_four_fields_preserves_yaml_comment_unknown_dates_and_body(self):
        self.assertEqual(form_fields(RAW), {"title": "文章", "description": "原摘要",
                                             "tags": ["一", "二"], "sticky": False})
        updated = patch_fields(RAW, {"title": "新标题", "description": "新摘要\n第二行",
                                     "tags": ["新", "二"], "sticky": True})
        self.assertEqual(form_fields(updated), {"title": "新标题", "description": "新摘要\n第二行",
                                                 "tags": ["新", "二"], "sticky": True})
        for retained in ("# 保留标题注释", "# 组注释", "# 标签注释", "# 保留置顶注释",
                         "unknown: { nested: [1, 2] } # 保留未知", "# 代码示例",
                         'updated: "2026-11-07T10:00:00+08:00"', "# 新标题 ###", "正文"):
            self.assertIn(retained, updated)
        self.assertTrue(updated.startswith("\ufeff---\r\n"))
        self.assertNotIn("\n", updated.replace("\r\n", ""))
        self.assertEqual(parse_markdown(updated)[0]["unknown"], {"nested": [1, 2]})

    def test_shared_yaml_node_is_never_mutated_by_form(self):
        raw = RAW.replace("'文章' #", "&title '文章' #").replace(
            "unknown: { nested: [1, 2] }", "unknown: { nested: [*title] }")
        with self.assertRaises(ArticleError):
            patch_fields(raw, {"title": "替换"})

    def test_source_without_supported_fields_can_still_be_edited_as_source(self):
        with self.assertRaises(ArticleError):
            form_fields("# 无头部")
        self.assertEqual(patch_fields(RAW, {"title": "文章"}), RAW)

    def test_new_empty_draft_heading_and_six_field_order(self):
        raw = RAW.removeprefix("\ufeff").split("---\r\n\r\n", 1)[0] + "---\r\n\r\n# \r\n"
        updated = patch_fields(raw, {"title": "开始写作"})
        self.assertTrue(updated.endswith("# 开始写作\r\n"))


    def test_updates_first_setext_h1_without_creating_duplicate_heading(self):
        raw = RAW.replace("# 文章 ###\r\n", "文章\r\n===\r\n").replace("正文\r\n", "# 后续标题\r\n")
        updated = patch_fields(raw, {"title": "新标题"})
        self.assertIn("# 新标题\r\n\r\n# 后续标题", updated)
        self.assertNotIn("文章\r\n===", updated)
