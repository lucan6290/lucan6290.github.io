"""内容接口回归；所有写入限临时项目。"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app import create_app


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.content = self.root / "frontend" / "content"
        self.content.mkdir(parents=True)
        (self.root / "admin-desktop").mkdir()
        self.client = TestClient(create_app(self.root, "test-token"))
        self.client.headers["Authorization"] = "Bearer test-token"

    def write(self, path, raw):
        target = self.content / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw.encode("utf-8"))
        return target

    def read(self, path):
        return self.client.get("/api/v1/documents", params={"path": path})

    def save(self, path, raw, version):
        return self.client.put("/api/v1/documents", json={
            "relative_path": path, "raw_content": raw, "expected_version": version,
        })

    def test_health_identifies_root_and_other_routes_require_token(self):
        health = self.client.get("/health").json()
        self.assertEqual(health, {"service": "xiaocancoding-content", "api_version": 1,
                                 "project_root": str(self.root.resolve()),
                                 "content_root": str(self.content.resolve())})
        response = self.client.get("/api/v1/content", headers={"Authorization": "Bearer wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("code", response.json())

    def test_full_yaml_and_original_bytes_survive_body_edit(self):
        raw = '\ufeff---\r\n# preserve comment\r\ntitle: 测试\r\ntags: [Python, AI]\r\ncustom:\r\n  nested: [1, true]\r\ndate: 2026-10-29\r\n---\r\n# 正文\r\n旧内容\r\n'
        target = self.write("knowledge/01-中文 空格.md", raw)
        detail = self.read("knowledge/01-中文 空格.md").json()
        self.assertEqual(detail["raw_content"], raw)
        self.assertEqual(detail["tags"], ["Python", "AI"])
        self.assertEqual(detail["frontmatter"]["custom"], {"nested": [1, True]})
        self.assertEqual(detail["date"], "2026-10-29")
        self.assertEqual(detail["version"], hashlib.sha256(target.read_bytes()).hexdigest())
        updated = raw.replace("旧内容", "新内容")
        result = self.save(detail["relative_path"], updated, detail["version"])
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(target.read_bytes(), updated.encode("utf-8"))

    def test_no_change_save_does_not_replace_file(self):
        target = self.write("plain.md", "# 原文\n")
        detail = self.read("plain.md").json()
        before = target.stat().st_mtime_ns
        with patch("content_store.os.replace", side_effect=AssertionError("must not write")):
            response = self.save("plain.md", detail["raw_content"], detail["version"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(target.stat().st_mtime_ns, before)
        self.assertEqual(response.json()["frontmatter"], {})
        self.assertIsNone(response.json()["date"])

    def test_create_is_exclusive_normalizes_new_file_and_requires_parent(self):
        (self.content / "新栏目" / "01-目录 空格").mkdir(parents=True)
        payload = {"relative_path": "新栏目/01-目录 空格/01-测试.md", "raw_content": "\ufeff---\r\ntags: [AI]\r\n---\r\n# 标题\r\n", "article": False}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.client.post("/api/v1/documents", json=payload), range(2)))
        self.assertEqual(sorted(r.status_code for r in results), [201, 409])
        raw = (self.content / payload["relative_path"]).read_bytes()
        self.assertEqual(raw, b"---\ntags: [AI]\n---\n# " + "标题\n".encode())
        response = self.client.post("/api/v1/documents", json={"relative_path": "missing/a.md", "raw_content": "text", "article": False})
        self.assertEqual(response.status_code, 404)
        self.assertFalse((self.content / "missing").exists())

    def test_invalid_yaml_cannot_create_or_overwrite(self):
        target = self.write("note.md", "# safe\n")
        detail = self.read("note.md").json()
        invalid = "---\ntags: [broken\n---\n# text"
        response = self.save("note.md", invalid, detail["version"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("line", response.json()["details"])
        self.assertEqual(target.read_bytes(), b"# safe\n")
        response = self.client.post("/api/v1/documents", json={"relative_path": "bad.md", "raw_content": invalid, "article": False})
        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.content / "bad.md").exists())

    def test_invalid_yaml_date_is_400_and_does_not_block_content_list(self):
        raw = "---\ndate: 2026-02-30\n---\n# Invalid date\n"
        response = self.client.post("/api/v1/documents", json={"relative_path": "bad.md", "raw_content": raw, "article": False})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_yaml")
        self.assertFalse((self.content / "bad.md").exists())
        self.write("external.md", raw)
        self.write("valid.md", "# Valid\n")
        response = self.client.get("/api/v1/content")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({d["name"] for d in response.json()["documents"]}, {"external.md", "valid.md"})
        self.assertEqual(self.read("external.md").status_code, 400)

    def test_missing_version_and_external_update_preserve_disk(self):
        target = self.write("note.md", "# original\n")
        detail = self.read("note.md").json()
        response = self.client.put("/api/v1/documents", json={"relative_path": "note.md", "raw_content": "overwrite"})
        self.assertEqual(response.status_code, 428)
        target.write_bytes(b"# external\n")
        self.assertEqual(self.save("note.md", "overwrite", detail["version"]).status_code, 409)
        response = self.client.request("DELETE", "/api/v1/documents", json={"relative_path": "note.md", "expected_version": detail["version"], "confirm": True})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(target.read_bytes(), b"# external\n")

    def test_version_and_save_after_external_delete_do_not_recreate(self):
        target = self.write("note.md", "# original\n")
        detail = self.read("note.md").json()
        target.unlink()
        response = self.client.get("/api/v1/documents/version", params={"path": "note.md"})
        self.assertEqual(response.json(), {"exists": False, "version": None})
        self.assertEqual(self.save("note.md", "overwrite", detail["version"]).status_code, 404)
        self.assertFalse(target.exists())

    def test_delete_requires_confirmation_and_only_removes_document(self):
        target = self.write("topic/note.md", "# original\n")
        resource = self.write("topic/note-images/image.png", "image")
        version = self.read("topic/note.md").json()["version"]
        payload = {"relative_path": "topic/note.md", "expected_version": version, "confirm": False}
        self.assertEqual(self.client.request("DELETE", "/api/v1/documents", json=payload).status_code, 400)
        payload["confirm"] = True
        response = self.client.request("DELETE", "/api/v1/documents", json=payload)
        self.assertEqual(response.json(), {"deleted": "topic/note.md"})
        self.assertFalse(target.exists())
        self.assertTrue(resource.exists())

    def test_atomic_replace_failure_keeps_original_and_cleans_temp(self):
        target = self.write("note.md", "# safe\n")
        detail = self.read("note.md").json()
        with patch("content_store.os.replace", side_effect=OSError("simulated failure")):
            response = self.save("note.md", "# changed\n", detail["version"])
        self.assertEqual(response.status_code, 500)
        self.assertEqual(target.read_bytes(), b"# safe\n")
        self.assertEqual([p.name for p in self.content.iterdir()], ["note.md"])

    def test_create_write_failure_leaves_no_partial_document(self):
        with patch("content_store.os.fsync", side_effect=OSError("disk failure")):
            response = self.client.post("/api/v1/documents", json={"relative_path": "new.md", "raw_content": "# new", "article": False})
        self.assertEqual(response.status_code, 500)
        self.assertFalse((self.content / "new.md").exists())

    def test_existing_directory_cannot_be_read_as_document(self):
        (self.content / "folder.md").mkdir()
        response = self.read("folder.md")
        self.assertEqual(response.status_code, 400)

    def test_directory_parent_file_is_a_conflict(self):
        self.write("existing.md", "text")
        response = self.client.post("/api/v1/directories", json={"relative_path": "existing.md/nested"})
        self.assertEqual(response.status_code, 409)

    def test_version_detects_atomic_replacement_even_with_invalid_yaml(self):
        target = self.write("note.md", "# before\n")
        original = self.read("note.md").json()["version"]
        replacement = self.write("replacement.md", "---\ntags: [unfinished\n---\n")
        os.replace(replacement, target)
        version = self.client.get("/api/v1/documents/version", params={"path": "note.md"}).json()
        self.assertTrue(version["exists"])
        self.assertNotEqual(version["version"], original)
        self.assertEqual(self.read("note.md").status_code, 400)

    def test_invalid_yaml_and_utf8_do_not_hide_unrelated_documents(self):
        self.write("valid.md", "# Valid\n")
        self.write("invalid.md", "---\ntags: [unfinished\n---\n# Bad YAML\n")
        (self.content / "binary.md").write_bytes(b"\xff\xfe")
        response = self.client.get("/api/v1/content")
        self.assertEqual(response.status_code, 200)
        documents = {d["name"]: d for d in response.json()["documents"]}
        self.assertEqual(set(documents), {"valid.md", "invalid.md", "binary.md"})
        self.assertEqual(documents["invalid.md"]["title"], "Bad YAML")
        self.assertEqual(self.read("invalid.md").status_code, 400)
        self.assertEqual(self.read("binary.md").json()["code"], "invalid_encoding")

    def test_read_retries_when_file_changes_between_data_and_stat(self):
        target = self.write("note.md", "# old\n")
        original_fstat = os.fstat
        calls = 0

        def external_write(fileno):
            nonlocal calls
            calls += 1
            if calls == 2:
                target.write_bytes(b"# external longer\n")
            return original_fstat(fileno)

        with patch("content_store.os.fstat", side_effect=external_write):
            response = self.read("note.md")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["raw_content"], "# external longer\n")
        self.assertEqual(response.json()["version"], hashlib.sha256(b"# external longer\n").hexdigest())

    def test_same_version_concurrent_saves_have_one_winner(self):
        target = self.write("note.md", "# original\n")
        version = self.read("note.md").json()["version"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda text: self.save("note.md", text, version), ["# one\n", "# two\n"]))
        self.assertEqual(sorted(result.status_code for result in results), [200, 409])
        self.assertIn(target.read_bytes(), [b"# one\n", b"# two\n"])

    @unittest.skipUnless(shutil.which("node"), "frontend scanner comparison needs Node")
    def test_shared_fixture_matches_frontend_scanner_discovery_and_numeric_order(self):
        self.write("knowledge/01-topic/README.md", "# 目录介绍\n")
        self.write("knowledge/01-topic/02-second.md", "~~~md\n# Ignore\n~~~\n# Actual ##\n")
        self.write("knowledge/01-topic/01-first.md", "---\ntitle: 显式标题\ntags: [AI, Python]\n---\n# ignored\n")
        self.write("knowledge/assets/private.md", "# excluded\n")
        self.write("knowledge/01-topic/02-second-images/a.png", "resource")
        self.write("new-section/README.md", "# Dynamic\n")
        (self.content / "knowledge/02-empty").mkdir()
        (self.content / "new-section/empty-child").mkdir()
        (self.content / "empty-section").mkdir()
        (self.content / ".hidden").mkdir()
        scanner = BACKEND.parents[1] / "frontend/scripts/lib/buildContent.mjs"
        code = '''const {build} = await import(process.argv[1]);
console.log = () => {};
const result = build({contentDir: process.argv[2], outDir: process.argv[3]});
const directories = [], documents = [];
function walk(nodes) { for (const n of nodes) {
  if (n.article) documents.push([n.article.relativePath, n.article.frontmatter.title, n.article.frontmatter.tags]);
  else { directories.push(n.path.slice(1)); if (n.introduction) documents.push([n.introduction.relativePath, n.introduction.frontmatter.title, n.introduction.frontmatter.tags]); walk(n.children); }
} }
walk(result.tree); process.stdout.write(JSON.stringify({directories, documents}));'''
        result = subprocess.run(["node", "--input-type=module", "-e", code, scanner.as_uri(), str(self.content), str(self.root / "generated")], check=True, capture_output=True, encoding="utf-8")
        frontend = json.loads(result.stdout)
        backend = self.client.get("/api/v1/content").json()
        self.assertEqual([d["relative_path"] for d in backend["directories"]][1:], frontend["directories"])
        self.assertEqual(sorted([d["relative_path"], d["title"], d["tags"]] for d in backend["documents"]), sorted(frontend["documents"]))
        topic_docs = [d["name"] for d in backend["documents"] if d["relative_path"].startswith("knowledge/01-topic/") and d["kind"] == "article"]
        self.assertEqual(topic_docs, ["01-first.md", "02-second.md"])

    def test_unsafe_paths_are_rejected_on_reads_and_writes(self):
        paths = ["../escape.md", "/absolute.md", "C:/escape.md", "a/../b.md", "./a.md", "a\\b.md", ".hidden.md", "_hidden/x.md", "CON.md", "com1.md", "a./b.md", "a /b.md", "a:b.md", "a//b.md", "a?.md"]
        for value in paths:
            with self.subTest(path=value):
                self.assertEqual(self.read(value).status_code, 400)
                response = self.client.post("/api/v1/documents", json={"relative_path": value, "raw_content": "text", "article": False})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.read("image.png").status_code, 400)

    def test_symlink_escape_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "note.md").write_bytes(b"private")
        try:
            (self.content / "escape").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("environment does not permit symbolic links")
        self.assertEqual(self.read("escape/note.md").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/directories", json={"relative_path": "escape/new"}).status_code, 400)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_junction_escape_and_cycle_are_skipped_without_following_targets(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private.md").write_bytes(b"# private")
        self.write("knowledge/valid.md", "# valid")
        links = []
        try:
            for name, destination in [("01-outside", outside), ("02-cycle", self.content), ("03-internal", self.content / "knowledge")]:
                link = self.content / name
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(destination)], capture_output=True)
                if result.returncode:
                    self.skipTest("junction creation unavailable")
                links.append(link)
            response = self.client.get("/api/v1/content")
            self.assertEqual(response.status_code, 200)
            self.assertEqual([d["relative_path"] for d in response.json()["documents"]], ["knowledge/valid.md"])
            self.assertEqual([d["relative_path"] for d in response.json()["directories"]], ["", "knowledge"])
        finally:
            for link in links:
                # 仅删除明确创建的 junction 本身，不递归触碰目标目录。
                os.rmdir(link)
        self.assertTrue((outside / "private.md").exists())

    def test_explicit_directories_are_recursive_and_exclusive(self):
        response = self.client.post("/api/v1/directories", json={"relative_path": "新栏目/01-分类 空格"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"relative_path": "新栏目/01-分类 空格", "name": "01-分类 空格", "label": "分类 空格", "section": "新栏目"})
        self.assertEqual(self.client.post("/api/v1/directories", json={"relative_path": "新栏目/01-分类 空格"}).status_code, 409)

    def test_tree_distinguishes_readme_empty_directories_resources_and_mdx(self):
        self.write("knowledge/02-分类/readME.md", "# 简介\n")
        self.write("knowledge/02-分类/02-second.md", "```md\n# ignored\n```\n# 正确标题\n")
        self.write("knowledge/02-分类/01-first.mdx", "# MDX source\n")
        self.write("knowledge/02-分类/index.md", "text")
        self.write("knowledge/assets/hidden.md", "# Resource")
        self.write("knowledge/_private/hidden.md", "# Hidden")
        self.write("_private/hidden.md", "# Hidden root")
        self.write("knowledge/02-分类/02-second-images/a.png", "image")
        (self.content / "knowledge/01-empty").mkdir()
        (self.content / "新栏目").mkdir()
        self.write("01-root.md", "no heading")
        result = self.client.get("/api/v1/content").json()
        self.assertEqual([d["relative_path"] for d in result["directories"]], ["", "knowledge", "knowledge/01-empty", "knowledge/02-分类", "新栏目"])
        documents = {d["relative_path"]: d for d in result["documents"]}
        self.assertEqual(len(documents), 5)
        self.assertEqual(documents["knowledge/02-分类/readME.md"]["kind"], "introduction")
        self.assertEqual(documents["knowledge/02-分类/index.md"]["kind"], "article")
        self.assertEqual(documents["knowledge/02-分类/02-second.md"]["title"], "正确标题")
        self.assertEqual(documents["01-root.md"]["title"], "root")
        self.assertEqual(self.read("knowledge/02-分类/01-first.mdx").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/documents", json={"relative_path": "new.mdx", "raw_content": "# text", "article": False}).status_code, 400)

    def test_cors_restricts_browser_origin(self):
        headers = {"Origin": "http://127.0.0.1:14200", "Access-Control-Request-Method": "PUT"}
        self.assertEqual(self.client.options("/api/v1/documents", headers=headers).status_code, 200)
        headers["Origin"] = "https://untrusted.example"
        self.assertEqual(self.client.options("/api/v1/documents", headers=headers).status_code, 400)


class StartupTests(unittest.TestCase):
    def test_port_failure_does_not_replace_existing_session(self):
        import main
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "frontend/content").mkdir(parents=True)
            (root / "admin-desktop").mkdir()
            session_file = root / "session.json"
            main.prepare_session(root, session_file)
            before = session_file.read_bytes()
            args = ["main.py", "--project-root", str(root), "--session-file", str(session_file)]
            with patch.object(sys, "argv", args), patch("socket.socket.bind", side_effect=OSError("occupied")), patch("main.uvicorn.run", side_effect=SystemExit(3)), patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    main.main()
            self.assertTrue(session_file.read_bytes() == before, "失败启动必须保留原会话文件")

    def test_session_uses_explicit_root_random_token_and_no_secret_output(self):
        from main import prepare_session, resolve_project_root
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "frontend/content").mkdir(parents=True)
            (root / "admin-desktop").mkdir()
            self.assertEqual(resolve_project_root(root), root.resolve())
            path = root / "session/custom.json"
            first = prepare_session(root, path)
            second = prepare_session(root, path)
            self.assertNotEqual(first["token"], second["token"])
            self.assertGreaterEqual(len(second["token"]), 32)
            self.assertEqual(json.loads(path.read_text("utf-8")), second)
            with self.assertRaises(RuntimeError):
                resolve_project_root(root / "missing")

    def test_cli_fixed_port_reload_and_factory_keep_same_token(self):
        import main
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "frontend/content").mkdir(parents=True)
            (root / "admin-desktop").mkdir()
            session_file = root / "session.json"
            args = ["main.py", "--project-root", str(root), "--port", "18000", "--reload", "--session-file", str(session_file)]
            original_bind = socket.socket.bind
            listener = None

            def bind_temporary(sock, address):
                original_bind(sock, (address[0], 0) if address == ("127.0.0.1", 18000) else address)

            def run_reloader(reloader):
                nonlocal listener
                listener = reloader.sockets[0]
                self.assertNotEqual(listener.fileno(), -1)
                self.assertTrue(listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN))
                self.assertTrue(listener.get_inheritable())
                self.assertTrue(reloader.config.should_reload)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as competitor:
                    competitor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    with self.assertRaises(OSError):
                        competitor.bind(listener.getsockname())
                        competitor.listen(1)
                session = json.loads(session_file.read_text("utf-8"))
                for _ in range(2):
                    client = TestClient(main.create_runtime_app())
                    response = client.get("/api/v1/content", headers={"Authorization": f"Bearer {session['token']}"})
                    self.assertEqual(response.status_code, 200)
                self.assertEqual(reloader.config.port, 18000)

            with patch.object(sys, "argv", args), patch.dict(os.environ), patch("socket.socket.bind", new=bind_temporary), patch("main.ChangeReload.run", new=run_reloader):
                main.main()
            self.assertEqual(listener.fileno(), -1)
            with patch.object(sys, "argv", ["main.py", "--port", "18001"]), patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as error:
                    main.main()
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
