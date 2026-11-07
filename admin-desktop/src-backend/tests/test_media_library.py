import base64
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from content_store import ContentError, ContentStore
from media_library import MediaLibrary

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jE1sAAAAASUVORK5CYII="


class MediaLibraryTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.content = self.root / "frontend/content"
        (self.content / "blog").mkdir(parents=True)
        self.document = "blog/文章 一.md"
        self.write(self.document, "# 文章一")
        self.media = MediaLibrary(ContentStore(self.root))

    def write(self, path, text):
        (self.content / path).write_text(text, encoding="utf-8")

    def test_import_is_exclusive_and_returns_previewable_markdown(self):
        first = self.media.import_image(self.document, "截图 (1).PNG", PNG)
        second = self.media.import_image(self.document, "截图 (1).png", PNG)
        self.assertEqual(first["relative_path"], "blog/文章 一-images/截图 (1).PNG")
        self.assertEqual(second["relative_path"], "blog/文章 一-images/截图 (1)-2.png")
        self.assertEqual(first["markdown"], "![截图 (1)](./文章%20一-images/截图%20%281%29.PNG)")
        target, mime = self.media.store.image(first["relative_path"])
        self.assertEqual(target.read_bytes(), base64.b64decode(PNG))
        self.assertEqual(mime, "image/png")
        self.assertEqual({entry["relative_path"] for entry in self.media.list_images(self.document)}, {
            first["relative_path"], second["relative_path"],
        })

    def test_import_rejects_invalid_names_missing_article_and_disguised_files(self):
        for article, name, data in (
            (self.document, "../out.png", PNG),
            (self.document, "NUL.png", PNG),
            (self.document, "bad.jpg", PNG),
            (self.document, "bad.png", "not-base64!"),
            ("blog/不存在.md", "out.png", PNG),
            ("../../out.md", "out.png", PNG),
        ):
            with self.subTest(article=article, name=name):
                with self.assertRaises(ContentError):
                    self.media.import_image(article, name, data)
        self.assertEqual(sorted(p.name for p in (self.content / "blog").iterdir()), ["文章 一.md"])

    def test_active_svg_rejected_before_writing(self):
        malicious = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        with self.assertRaises(ContentError):
            self.media.import_image(self.document, "unsafe.svg", base64.b64encode(malicious).decode())
        self.assertFalse((self.content / "blog/文章 一-images").exists())

    def test_delete_reports_refs_and_refuses_stale_plan(self):
        image = self.media.import_image(self.document, "图.png", PNG)
        self.write(self.document, f"# 文章一\n\n{image['markdown']}\n")
        plan = self.media.delete_plan(image["relative_path"])
        self.assertEqual(plan["references"], [{"relative_path": self.document, "count": 1}])
        self.write("blog/另 一.md", "[下载](<./文章 一-images/图.png>)")
        with self.assertRaises(ContentError) as caught:
            self.media.delete(image["relative_path"], plan["plan_id"], True)
        self.assertEqual(caught.exception.status, 409)
        target = self.content / image["relative_path"]
        self.assertTrue(target.is_file())
        new = self.media.delete_plan(image["relative_path"])
        with self.assertRaises(ContentError):
            self.media.delete(image["relative_path"], new["plan_id"], False)
        self.media.delete(image["relative_path"], new["plan_id"], True)
        self.assertFalse(target.exists())
        self.assertIn(image["markdown"], (self.content / self.document).read_text(encoding="utf-8"))


    def test_media_http_routes_require_session_and_share_existing_preview(self):
        from fastapi.testclient import TestClient
        from app import create_app

        with TestClient(create_app(self.root, "media-test")) as client:
            data = {"document_path": self.document, "filename": "图片.png", "data_base64": PNG}
            self.assertEqual(client.post("/api/v1/media", json=data).status_code, 401)
            headers = {"Authorization": "Bearer media-test"}
            imported = client.post("/api/v1/media", json=data, headers=headers)
            self.assertEqual(imported.status_code, 201, imported.text)
            path = imported.json()["relative_path"]
            image = client.get("/api/v1/images", params={"path": path}, headers=headers)
            self.assertEqual(image.content, base64.b64decode(PNG))
            self.assertEqual(image.headers["content-type"], "image/png")
            listed = client.get("/api/v1/media", params={"document_path": self.document}, headers=headers)
            self.assertEqual(listed.json()["images"][0]["relative_path"], path)
