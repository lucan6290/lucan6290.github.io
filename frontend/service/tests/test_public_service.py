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


ARTICLE = "blog/01-分 类/01-标题.md"
OTHER_ARTICLE = "knowledge/另一篇.md"
SITE = "https://site.example.test"
BASE = "/api/v1"


class PublicServiceTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = self.root / "content-manifest.json"
        articles = {f"/{path[:-3]}": {"relativePath": path} for path in (ARTICLE, OTHER_ARTICLE)}
        self.manifest.write_text(json.dumps({"articles": articles}), encoding="utf-8")
        self.token = uuid4().hex + uuid4().hex
        self.settings = Settings(SITE, self.manifest, self.root / "interactions.sqlite3", self.token)
        self.client = self.open_client()
        self.admin = {"Authorization": f"Bearer {self.token}"}

    def open_client(self):
        client = TestClient(create_app(self.settings))
        self.addCleanup(client.close)
        return client

    def article(self, path=ARTICLE, **query):
        return self.client.get(f"{BASE}/article", params={"article_path": path, **query})

    def view(self, session, path=ARTICLE):
        return self.client.post(f"{BASE}/views", json={"article_path": path, "session_id": str(session)})

    def submit(self, body, submission_id=None):
        return self.client.post(f"{BASE}/comments", json={
            "article_path": ARTICLE, "body": body, "submission_id": str(submission_id or uuid4()),
        })

    def test_same_session_is_counted_once_even_under_concurrency_and_after_restart(self):
        session = uuid4()
        with ThreadPoolExecutor(max_workers=8) as workers:
            responses = list(workers.map(self.view, [session] * 8))
        self.assertEqual([(r.status_code, r.json()) for r in responses], [(200, {"views": 1})] * 8)
        self.client = self.open_client()
        self.assertEqual(self.view(session).json(), {"views": 1})
        self.assertEqual(self.view(uuid4()).json(), {"views": 2})
        self.assertEqual(self.view(session, OTHER_ARTICLE).json(), {"views": 1})
        self.assertEqual(self.article().json(), {"views": 2, "comments": [], "next_before": None})

    def test_only_exact_published_paths_are_accepted(self):
        for path in ("blog/draft.md", "blog/README.md", ARTICLE.upper(), f"/{ARTICLE}", f"blog/../{ARTICLE}", ARTICLE.replace(" ", "%20")):
            with self.subTest(path=path):
                self.assertEqual(self.article(path).status_code, 404)
                self.assertEqual(self.view(uuid4(), path).status_code, 404)
        self.assertEqual(self.article().json()["views"], 0)

    def test_anonymous_text_requires_approval_and_can_be_withdrawn(self):
        body = "<img src=x onerror=alert(1)>\n第二行"
        response = self.submit(body)
        self.assertEqual((response.status_code, response.json()), (201, {"status": "accepted"}))
        self.client = self.open_client()
        self.assertEqual(self.article().json()["comments"], [])
        queue = f"{BASE}/admin/comments"
        self.assertEqual(self.client.get(queue).status_code, 401)
        self.assertEqual(self.client.get(queue, headers={"Authorization": "Bearer wrong"}).status_code, 401)
        comment = self.client.get(queue, headers=self.admin).json()["comments"][0]
        self.assertEqual(comment["article_path"], ARTICLE)
        edit = f"{queue}/{comment['id']}"
        self.assertEqual(self.client.patch(edit, json={"status": "published"}).status_code, 401)
        self.assertEqual(self.client.patch(edit, headers=self.admin, json={"status": "published"}).status_code, 200)
        [published] = self.article().json()["comments"]
        self.assertEqual(published, {"id": comment["id"], "body": body, "created_at": comment["created_at"]})
        self.assertEqual(self.client.patch(edit, headers=self.admin, json={"status": "rejected"}).status_code, 200)
        self.assertEqual(self.article().json()["comments"], [])

    def test_rejects_invalid_input_without_echoing_and_throttles_comments(self):
        for invalid in (" ", "\x00", "密" * 2001):
            with self.subTest(length=len(invalid)):
                response = self.submit(invalid)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(set(response.json()), {"code", "message"})
        self.assertEqual(self.view("fake").status_code, 422)
        for _ in range(5):
            self.assertEqual(self.submit("评论").status_code, 201)
        self.client = self.open_client()
        self.assertEqual(self.submit("第六条").status_code, 429)

    def test_comment_retry_does_not_add_another_review_item(self):
        submission_id = uuid4()
        self.assertEqual(self.submit("留言", submission_id).status_code, 201)
        self.client = self.open_client()
        self.assertEqual(self.submit("留言", submission_id).status_code, 201)
        self.assertEqual(self.submit("不同正文", submission_id).status_code, 409)
        queue = self.client.get(f"{BASE}/admin/comments", headers=self.admin).json()["comments"]
        self.assertEqual([comment["body"] for comment in queue], ["留言"])

    def test_exact_origin_cors_rejects_foreign_requests_and_does_not_cache(self):
        url = f"{BASE}/comments"
        preflight = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"}
        allowed = self.client.options(url, headers={"Origin": SITE, **preflight})
        self.assertEqual(allowed.headers["Access-Control-Allow-Origin"], SITE)
        foreign = self.client.options(url, headers={"Origin": f"{SITE}.evil.test", **preflight})
        self.assertEqual(foreign.status_code, 400)
        denied = self.client.post(url, headers={"Origin": "https://elsewhere.example.test"},
                                  json={"article_path": ARTICLE, "body": "不能写入"})
        self.assertEqual(denied.status_code, 403)
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)
        self.assertEqual(self.client.get(f"{BASE}/admin/comments", headers=self.admin).json()["comments"], [])
        self.assertEqual(self.article().headers["Cache-Control"], "no-store")

    def test_payload_limit_applies_to_declared_and_streamed_bodies(self):
        url = f"{BASE}/comments"
        body = b"x" * 65536
        self.assertEqual(self.client.post(url, content=body, headers={"Content-Type": "application/json"}).status_code, 413)
        stream = (b"x" * 32768 for _ in range(2))
        self.assertEqual(self.client.post(url, content=stream, headers={"Content-Type": "application/json"}).status_code, 413)
