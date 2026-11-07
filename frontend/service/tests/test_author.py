import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_api import Settings, create_app


BASE = "/api/v1/admin"
PATH = "blog/01-线上笔记.md"
RAW = """---
title: "线上笔记"
date: "2026-10-29T10:00:00+08:00"
updated: "2026-10-29T10:00:00+08:00"
description: "文章摘要。"
tags: []
sticky: false
---

# 线上笔记
"""


class AuthorTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.content = self.root / "frontend" / "content"
        (self.content / "blog").mkdir(parents=True)
        (self.content / "blog" / "images").mkdir()
        self.manifest = self.root / "content-manifest.json"
        self.manifest.write_text(json.dumps({"articles": {}}), encoding="utf-8")
        self.token = uuid4().hex + uuid4().hex
        self.admin = {"Authorization": f"Bearer {self.token}"}

    def client(self, *, writing=True, admin=True):
        settings = Settings(
            "https://site.example.test", self.manifest, self.root / "interactions.sqlite3",
            self.token if admin else "", author_project_root=self.root if writing else None,
        )
        client = TestClient(create_app(settings))
        self.addCleanup(client.close)
        return client

    def create(self, client, raw=RAW, path=PATH):
        return client.post(f"{BASE}/documents", headers=self.admin,
                           json={"relative_path": path, "raw_content": raw})

    def save(self, client, raw, version, path=PATH):
        return client.put(f"{BASE}/document", headers=self.admin,
                          json={"relative_path": path, "raw_content": raw, "expected_version": version})

    def test_authentication_required_and_authoring_can_be_disabled(self):
        client = self.client()
        self.assertEqual(client.get(f"{BASE}/session").status_code, 401)
        self.assertEqual(client.get(f"{BASE}/documents").status_code, 401)
        self.assertEqual(client.post(f"{BASE}/documents", json={"relative_path": PATH, "raw_content": RAW}).status_code, 401)
        self.assertFalse((self.content / PATH).exists())
        session = client.get(f"{BASE}/session", headers=self.admin)
        self.assertEqual(session.json(), {"writing_enabled": True})
        self.assertEqual(session.headers["Cache-Control"], "no-store")
        disabled = self.client(writing=False)
        self.assertEqual(disabled.get(f"{BASE}/session", headers=self.admin).json(), {"writing_enabled": False})
        self.assertEqual(self.create(disabled).status_code, 503)
        self.assertEqual(self.client(admin=False, writing=False).get(f"{BASE}/session", headers=self.admin).status_code, 503)

    def test_create_open_list_and_versioned_save_use_canonical_markdown(self):
        client = self.client()
        created = self.create(client)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(self.create(client).status_code, 409)
        self.assertEqual((self.content / PATH).read_text(encoding="utf-8"), RAW)
        listed = client.get(f"{BASE}/documents", headers=self.admin).json()
        self.assertEqual(listed["documents"], [{"relative_path": PATH, "title": "线上笔记"}])
        opened = client.get(f"{BASE}/document", headers=self.admin, params={"relative_path": PATH}).json()
        self.assertEqual(opened["raw_content"], RAW)
        self.assertEqual(opened["version"], created.json()["version"])
        saved = self.save(client, RAW + "\n新段落。\n", opened["version"])
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotEqual(saved.json()["version"], opened["version"])
        self.assertEqual((self.content / PATH).read_text(encoding="utf-8"), saved.json()["raw_content"])
        self.assertEqual(self.save(client, RAW, opened["version"]).status_code, 409)
        self.assertIn("新段落。", (self.content / PATH).read_text(encoding="utf-8"))
        self.assertIn('date: "2026-10-29T10:00:00+08:00"', saved.json()["raw_content"])
        article = client.get("/api/v1/article", params={"article_path": PATH})
        self.assertEqual(article.status_code, 404)

    def test_parallel_saves_of_same_version_do_not_overwrite_the_winner(self):
        client = self.client()
        version = self.create(client).json()["version"]
        with ThreadPoolExecutor(max_workers=2) as workers:
            responses = list(workers.map(lambda body: self.save(client, RAW + body, version), ["甲\n", "乙\n"]))
        self.assertEqual(sorted(r.status_code for r in responses), [200, 409])
        winner = next(r for r in responses if r.status_code == 200)
        self.assertEqual((self.content / PATH).read_text(encoding="utf-8"), winner.json()["raw_content"])

    def test_invalid_input_and_path_are_rejected_before_writing(self):
        client = self.client()
        invalid = self.create(client, RAW.replace("文章摘要。", ""))
        self.assertEqual((invalid.status_code, invalid.json()["code"]), (400, "invalid_article"))
        for path in ("../secret.md", "blog/_private.md", "blog/images/secret.md", "blog/evil.txt"):
            with self.subTest(path=path):
                self.assertEqual(self.create(client, path=path).status_code, 400)
        self.assertFalse((self.content / PATH).exists())
        self.assertEqual(self.create(client).status_code, 201)
        self.assertEqual(self.save(client, RAW + "新内容", None).status_code, 428)
        self.assertEqual((self.content / PATH).read_text(encoding="utf-8"), RAW)
