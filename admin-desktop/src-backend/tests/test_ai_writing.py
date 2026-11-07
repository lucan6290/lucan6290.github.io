import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ModelHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers["Content-Length"])
        self.server.calls.append((self.path, self.headers.get("Authorization"), json.loads(self.rfile.read(size))))
        status, headers, body = self.server.answer
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *_):
        pass


class AiWritingTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state_dir = Path(self.directory.name)
        self.model = ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
        self.model.calls = []
        self.model.answer = (200, {}, json.dumps({
            "choices": [{"message": {"content": "# 新正文\n\n复查后的内容。"}, "finish_reason": "stop"}],
        }).encode())
        self.worker = Thread(target=self.model.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.worker.start()
        self.addCleanup(self.stop_model)
        self.base_url = f"http://127.0.0.1:{self.model.server_port}/v1"

    def stop_model(self):
        self.model.shutdown()
        self.model.server_close()
        self.worker.join()

    def client(self):
        from ai_routes import create_ai_router
        from content_store import ContentError

        app = FastAPI()

        @app.exception_handler(ContentError)
        async def content_error(_request, error):
            return JSONResponse(status_code=error.status, content={"code": error.code, "message": error.message})

        app.include_router(create_ai_router(self.state_dir))
        return TestClient(app)

    def configure(self, client, **overrides):
        return client.put("/api/v1/ai/settings", json={"base_url": self.base_url, "model": "test-model", **overrides})

    def compose(self, client, **overrides):
        return client.post("/api/v1/ai/compose", json={
            "operation": "rewrite", "instruction": "压缩并保留术语", "body": "这是未保存的正文。",
            **overrides,
        })

    def test_rewrite_and_connection_test_use_actual_loopback_chat_completions(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        self.assertEqual(client.post("/api/v1/ai/test").json(), {"ok": True})
        response = self.compose(client)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"markdown": "# 新正文\n\n复查后的内容。"})
        path, auth, payload = self.model.calls[-1]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertIsNone(auth)
        self.assertEqual(payload["model"], "test-model")
        self.assertFalse(payload["stream"])
        self.assertIn("压缩并保留术语", payload["messages"][1]["content"])
        self.assertIn("这是未保存的正文。", payload["messages"][1]["content"])
        self.assertNotIn("这是未保存的正文。", json.dumps(self.model.calls[0], ensure_ascii=False))
        self.assertEqual(self.model.calls[0][2]["max_completion_tokens"], 32)

    def test_generate_never_sends_existing_body(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        self.assertEqual(self.compose(client, operation="generate", body=None).status_code, 200)
        self.assertNotIn("这是未保存的正文。", json.dumps(self.model.calls, ensure_ascii=False))
        self.assertEqual(self.compose(client, operation="generate").status_code, 400)
        self.assertEqual(len(self.model.calls), 1)

    def test_invalid_endpoint_does_not_change_existing_settings(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        for address in ("http://localhost/v1", "http://example.test/v1", "http://127.1/v1",
                        "https://secret@example.test/v1", "https://example.test/v1?token=secret",
                        "https://example.test/v1#secret", "https://@example.test/v1",
                        "https://example.test\\@127.0.0.1/v1"):
            with self.subTest(address=address):
                response = self.configure(client, base_url=address)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn("secret", response.text)
        self.assertEqual(client.get("/api/v1/ai/settings").json()["base_url"], self.base_url)

    def test_validation_does_not_echo_inputs_or_unknown_fields(self):
        client = self.client()
        response = self.configure(client, api_key={"private-marker": "private-value"}, **{"private-field": "secret"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_request")
        for secret in ("private-marker", "private-value", "private-field", "secret"):
            self.assertNotIn(secret, response.text)

    def test_session_key_is_never_stored_or_returned_and_old_endpoint_loses_key(self):
        client = self.client()
        private = "private-session-key"
        remote = "https://example.test/v1"
        response = self.configure(client, base_url=remote, api_key=private)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["key_mode"], "session")
        self.assertNotIn(private, response.text)
        self.assertNotIn(private, client.get("/api/v1/ai/settings").text)
        for path in self.state_dir.iterdir():
            self.assertNotIn(private.encode(), path.read_bytes())
        self.assertEqual(self.client().get("/api/v1/ai/settings").json()["key_mode"], "none")
        self.assertEqual(self.configure(client, base_url=remote, model="new-model").json()["key_mode"], "session")
        self.assertEqual(self.configure(client).json()["key_mode"], "none")
        self.assertEqual(self.configure(client, api_key=private).status_code, 400)
        self.assertEqual(self.configure(client, base_url=remote).json()["key_mode"], "none")

    @unittest.skipUnless(sys.platform == "win32", "requires Windows DPAPI")
    def test_windows_key_round_trips_for_current_user_and_is_explicitly_forgotten(self):
        from ai_writing import AiSettingsStore

        client = self.client()
        private = "private-windows-key"
        remote = "https://example.test/v1"
        response = self.configure(client, base_url=remote, api_key=private, key_mode="windows")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["key_mode"], "windows")
        self.assertNotIn(private, response.text)
        self.assertNotIn(private.encode(), (self.state_dir / "ai-settings.json").read_bytes())
        self.assertEqual(AiSettingsStore(self.state_dir).provider().api_key, private)
        self.assertEqual(self.configure(client, base_url=remote, key_mode="clear").json()["key_mode"], "none")
        self.assertIsNone(AiSettingsStore(self.state_dir).provider().api_key)

    def test_redirect_is_never_followed_and_upstream_error_is_not_reflected(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        self.model.answer = (307, {"Location": self.base_url + "/secret-hop"}, b"secret from provider")
        response = self.compose(client)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "ai_redirect")
        self.assertNotIn("secret", response.text)
        self.assertEqual(len(self.model.calls), 1)

    def test_provider_auth_failure_hides_body(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        self.model.answer = (401, {}, b"secret from provider")
        response = self.compose(client)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "ai_provider_auth")
        self.assertNotIn("secret", response.text)

    def test_truncated_invalid_and_oversized_outputs_are_rejected(self):
        client = self.client()
        self.assertEqual(self.configure(client).status_code, 200)
        for raw, code in [
            (b"z" * (1024 * 1024 + 1), "ai_response_too_large"),
            (b"secret non-JSON output", "ai_invalid_response"),
            (b'{"choices":[{"finish_reason":"length","message":{"content":"partial"}}]}', "ai_incomplete_response"),
            (b'{"choices":[{"message":{"content":"  "}}]}', "ai_invalid_response"),
        ]:
            with self.subTest(code=code):
                self.model.answer = (200, {}, raw)
                response = self.compose(client)
                self.assertEqual(response.status_code, 502)
                self.assertEqual(response.json()["code"], code)
                self.assertNotIn("secret", response.text)