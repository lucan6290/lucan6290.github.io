"""文章六字段与原文保留回归，所有写入使用临时项目。"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from content_store import ContentStore


ARTICLE = '''---
title: "我的文章"
date: "2026-10-29T10:00:00+08:00"
updated: "2026-10-29T10:00:00+08:00"
description: "文章摘要"
tags: ["学习笔记", "工程实践"]
sticky: false
---

# 我的文章

正文
'''


class ArticleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.content = self.root / "frontend/content"
        self.content.mkdir(parents=True)
        (self.root / "admin-desktop").mkdir()
        self.client = TestClient(create_app(self.root, "test-token"))
        self.client.headers["Authorization"] = "Bearer test-token"

    def create(self, raw=ARTICLE, path="article.md", **extra):
        return self.client.post("/api/v1/documents", json={
            "relative_path": path, "raw_content": raw, **extra,
        })

    def write(self, raw=ARTICLE, path="article.md"):
        target = self.content / path
        target.write_bytes(raw.encode("utf-8"))
        return target, self.client.get("/api/v1/documents", params={"path": path}).json()

    def save(self, detail, raw, **extra):
        return self.client.put("/api/v1/documents", json={
            "relative_path": detail["relative_path"], "raw_content": raw,
            "expected_version": detail["version"], **extra,
        })

    def test_default_create_requires_article_and_preserves_supplied_writing_time(self):
        response = self.create("# 普通文章\n")
        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.content / "article.md").exists())
        response = self.create()
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["raw_content"], ARTICLE)
        self.assertEqual(response.json()["date"], "2026-10-29T10:00:00+08:00")

    def test_store_default_create_enforces_article(self):
        from content_store import ContentError
        with self.assertRaises(ContentError):
            ContentStore(self.root).create("article.md", "# 原文")

    def test_explicit_document_and_case_insensitive_special_files_are_exempt(self):
        raw = "---\ntitle: 工程说明\n---\n# 原文\n"
        for path, extra in [("design.md", {"article": False}), ("readME.md", {}), ("AgEnTs.MD", {})]:
            with self.subTest(path=path):
                result = self.create(raw, path, **extra)
                self.assertEqual(result.status_code, 201, result.text)
                self.assertEqual(result.json()["raw_content"], raw)

    def test_article_flag_is_strict_on_create_and_save(self):
        for value in ["false", 0, None]:
            with self.subTest(value=value):
                self.assertEqual(self.create(article=value).status_code, 400)
        _, detail = self.write()
        for value in ["false", 0]:
            with self.subTest(value=value):
                self.assertEqual(self.save(detail, ARTICLE, article=value).status_code, 400)

    def test_explicit_document_save_preserves_full_frontmatter_as_original(self):
        target, detail = self.write()
        raw = ARTICLE.replace("正文", "说明正文").replace('title: "我的文章"\n', '')
        response = self.save(detail, raw, article=False)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(target.read_bytes(), raw.encode())
        self.assertEqual(response.json()["updated"], detail["updated"])

    def test_explicit_article_save_validates_and_maintains_dates(self):
        target, detail = self.write()
        self.assertEqual(self.save(detail, ARTICLE.replace('title: "我的文章"\n', ''), article=True).status_code, 400)
        self.assertEqual(target.read_bytes(), ARTICLE.encode())
        response = self.save(detail, ARTICLE.replace("正文", "修改正文"), article=True)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["date"], detail["date"])
        self.assertNotEqual(response.json()["updated"], detail["updated"])

    def test_explicit_article_can_complete_known_history_without_guessing_date(self):
        _, detail = self.write("# 历史文章\n")
        response = self.save(detail, ARTICLE, article=True)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["date"], "2026-10-29T10:00:00+08:00")

    def test_explicit_article_cannot_replace_existing_invalid_date(self):
        raw = ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"', 'date: "unknown"')
        target, detail = self.write(raw)
        result = self.save(detail, ARTICLE, article=True)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(target.read_bytes(), raw.encode())

    def test_new_article_rejects_missing_invalid_or_duplicate_fields(self):
        invalid = [
            ARTICLE.replace('title: "我的文章"\n', ""),
            ARTICLE.replace('title: "我的文章"', 'title: ""'),
            ARTICLE.replace('description: "文章摘要"', 'description: "  "'),
            ARTICLE.replace('title: "我的文章"', "title: 我的文章"),
            ARTICLE.replace('title: "我的文章"', "title: '我的文章'"),
            ARTICLE.replace('description: "文章摘要"', 'description: 42'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags: ["重复", "重复"]'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags: [""]'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags: ["   "]'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags: [42]'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags: [学习笔记]'),
            ARTICLE.replace('title: "我的文章"', 'title: &heading "我的文章"').replace('tags: ["学习笔记", "工程实践"]', 'tags: [*heading]'),
            ARTICLE.replace('tags: ["学习笔记", "工程实践"]', 'tags:\n  - "学习笔记"'),
            ARTICLE.replace('sticky: false', 'sticky: "false"'),
            ARTICLE.replace('sticky: false', 'sticky: 0'),
            ARTICLE.replace('sticky: false', 'sticky: no'),
            ARTICLE.replace('sticky: false', 'sticky: false\ntitle: "我的文章"'),
            ARTICLE.replace('title: "我的文章"\ndate:', 'date:').replace('description:', 'title: "我的文章"\ndescription:'),
            ARTICLE.replace('# 我的文章', '# 不同标题'),
            ARTICLE.replace('# 我的文章', '## 我的文章'),
        ]
        for raw in invalid:
            with self.subTest(raw=raw):
                response = self.create(raw)
                self.assertEqual(response.status_code, 400, response.text)
                self.assertFalse((self.content / "article.md").exists())

    def test_new_article_rejects_invalid_dates_and_legacy_fields(self):
        for date in ["2026-02-30T10:00:00+08:00", "2026-10-29", "2026-10-29T10:00:00Z", "2026-10-29T10:00:00.000+08:00"]:
            with self.subTest(date=date):
                self.assertEqual(self.create(ARTICLE.replace("2026-10-29T10:00:00+08:00", date)).status_code, 400)
        self.assertEqual(self.create(ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: "2026-10-29T11:00:00+08:00"')).status_code, 400)
        for field in ["authors", "slug", "sidebar_position", "created", "createdAt"]:
            with self.subTest(field=field):
                raw = ARTICLE.replace('sticky: false', f'sticky: false\n{field}: "旧值"')
                self.assertEqual(self.create(raw).status_code, 400)

    def test_empty_tags_unknown_fields_and_real_numeric_titles_are_valid(self):
        raw = ARTICLE.replace('["学习笔记", "工程实践"]', '[]').replace('sticky: false', 'sticky: false\ncustom: {nested: [1, true]}').replace("我的文章", "2026-10-29复盘")
        self.assertEqual(self.create(raw).status_code, 201)

    def test_actual_edit_changes_only_updated_value_and_retains_source_format(self):
        raw = "\ufeff" + ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: "2026-10-29T10:00:00+08:00" # 保留注释').replace('sticky: false', 'sticky: false\n# 未知字段\ncustom: {nested: [1, true]}').replace("\n", "\r\n")
        target, detail = self.write(raw)
        before = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0)
        response = self.save(detail, raw.replace("正文", "修改正文"))
        after = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0)
        self.assertEqual(response.status_code, 200, response.text)
        updated = response.json()["updated"]
        self.assertGreaterEqual(datetime.fromisoformat(updated), before)
        self.assertLessEqual(datetime.fromisoformat(updated), after)
        expected = raw.replace("正文", "修改正文").replace('updated: "2026-10-29T10:00:00+08:00"', f'updated: "{updated}"')
        self.assertEqual(target.read_bytes(), expected.encode("utf-8"))
        self.assertEqual(response.json()["date"], "2026-10-29T10:00:00+08:00")

    def test_metadata_edit_also_updates_time(self):
        _, detail = self.write()
        result = self.save(detail, ARTICLE.replace("文章摘要", "实际摘要修改"))
        self.assertEqual(result.status_code, 200)
        self.assertNotEqual(result.json()["updated"], detail["updated"])

    def test_unchanged_or_updated_only_edit_does_not_write_or_fake_time(self):
        for raw in [ARTICLE, ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: "2026-10-29T11:00:00+08:00"')]:
            with self.subTest(raw=raw):
                target, detail = self.write()
                before = target.stat().st_mtime_ns
                with patch("content_store.os.replace", side_effect=AssertionError("no write")):
                    result = self.save(detail, raw)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["raw_content"], ARTICLE)
                self.assertEqual(target.stat().st_mtime_ns, before)

    def test_date_change_and_required_field_removal_are_rejected(self):
        target, detail = self.write()
        invalid = [ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"', 'date: "2026-10-28T10:00:00+08:00"')]
        invalid.extend("\n".join(line for line in ARTICLE.split("\n") if not line.startswith(field + ":")) for field in ["title", "date", "updated", "description", "tags", "sticky"])
        for raw in invalid:
            with self.subTest(raw=raw):
                self.assertEqual(self.save(detail, raw).status_code, 400)
                self.assertEqual(target.read_bytes(), ARTICLE.encode("utf-8"))

    def test_historical_and_special_documents_do_not_gain_dates(self):
        for path, raw in [("old.md", '---\ntitle: 旧文章\n---\n正文\n'), ("README.md", ARTICLE), ("agents.md", ARTICLE)]:
            with self.subTest(path=path):
                target, detail = self.write(raw, path)
                edited = raw.replace("正文", "修改正文")
                response = self.save(detail, edited)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(target.read_bytes(), edited.encode("utf-8"))

    def test_conflict_checks_precede_article_validation_and_do_not_write(self):
        target, detail = self.write()
        target.write_bytes(ARTICLE.replace("正文", "外部正文").encode())
        self.assertEqual(self.save(detail, "invalid article").status_code, 409)
        self.assertEqual(target.read_bytes(), ARTICLE.replace("正文", "外部正文").encode())

    def test_update_cannot_precede_future_writing_date(self):
        raw = ARTICLE.replace("2026-10-29T10:00:00+08:00", "2099-01-01T00:00:00+08:00")
        _, detail = self.write(raw)
        response = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["updated"], "2099-01-01T00:00:00+08:00")

    def test_historical_complete_article_keeps_field_order_and_block_tags(self):
        raw = ARTICLE.replace('title: "我的文章"\n', '').replace('sticky: false', 'sticky: false\ntitle: 我的文章').replace('tags: ["学习笔记", "工程实践"]', 'tags:\n  - 学习笔记\n  - 工程实践')
        target, detail = self.write(raw)
        result = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(result.status_code, 200, result.text)
        expected = raw.replace("正文", "修改正文").replace('updated: "2026-10-29T10:00:00+08:00"', f'updated: "{result.json()["updated"]}"')
        self.assertEqual(target.read_bytes(), expected.encode())

    def test_invalid_existing_date_requires_author_confirmation(self):
        raw = ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"', 'date: "unknown"')
        target, detail = self.write(raw)
        result = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(result.status_code, 400)
        self.assertEqual(target.read_bytes(), raw.encode())

    def test_updated_alias_cannot_rewrite_original_date(self):
        raw = ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"', 'date: &start "2026-10-29T10:00:00+08:00"').replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: *start')
        target, detail = self.write(raw)
        result = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(result.status_code, 400)
        self.assertEqual(target.read_bytes(), raw.encode())

    def test_updated_anchor_is_preserved_when_only_its_value_changes(self):
        raw = ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: &last "2026-10-29T10:00:00+08:00"')
        target, detail = self.write(raw)
        result = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(result.status_code, 200, result.text)
        expected = raw.replace("正文", "修改正文").replace('updated: &last "2026-10-29T10:00:00+08:00"', f'updated: &last "{result.json()["updated"]}"')
        self.assertEqual(target.read_bytes(), expected.encode())

    def test_date_alias_to_updated_cannot_change_writing_time(self):
        raw = ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"\nupdated: "2026-10-29T10:00:00+08:00"', 'updated: &last "2026-10-29T10:00:00+08:00"\ndate: *last')
        target, detail = self.write(raw)
        result = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json()["code"], "invalid_article")
        self.assertEqual(target.read_bytes(), raw.encode())

    def test_other_metadata_aliases_to_updated_cannot_change_indirectly(self):
        for custom in ['custom: *last', 'custom: {nested: [*last]}']:
            with self.subTest(custom=custom):
                raw = ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: &last "2026-10-29T10:00:00+08:00"').replace('sticky: false', 'sticky: false\n' + custom)
                target, detail = self.write(raw)
                result = self.save(detail, raw.replace("正文", "修改正文"))
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.json()["code"], "invalid_article")
                self.assertEqual(target.read_bytes(), raw.encode())

    def test_merged_updated_must_be_an_independent_root_field(self):
        raw = ARTICLE.replace('title: "我的文章"', 'fields: &fields\n  updated: "2026-10-29T10:00:00+08:00"\n<<: *fields\ntitle: "我的文章"').replace('updated: "2026-10-29T10:00:00+08:00"\ndescription:', 'description:')
        target, detail = self.write(raw)
        response = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_article")
        self.assertEqual(target.read_bytes(), raw.encode())

    def test_shared_updated_alias_can_be_repaired_to_independent_values(self):
        old = ARTICLE.replace('date: "2026-10-29T10:00:00+08:00"\nupdated: "2026-10-29T10:00:00+08:00"', 'updated: &last "2026-10-29T10:00:00+08:00"\ndate: *last')
        target, detail = self.write(old)
        response = self.save(detail, ARTICLE.replace("正文", "修改正文"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["date"], "2026-10-29T10:00:00+08:00")
        self.assertIn(b"updated: \"", target.read_bytes())

    def test_root_metadata_key_alias_to_updated_cannot_change_indirectly(self):
        raw = ARTICLE.replace('updated: "2026-10-29T10:00:00+08:00"', 'updated: &last "2026-10-29T10:00:00+08:00"').replace('sticky: false', 'sticky: false\n*last : "用户自定义值"')
        target, detail = self.write(raw)
        response = self.save(detail, raw.replace("正文", "修改正文"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_article")
        self.assertEqual(target.read_bytes(), raw.encode())
