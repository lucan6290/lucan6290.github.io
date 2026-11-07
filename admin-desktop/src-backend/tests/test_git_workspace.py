import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from content_store import ContentError
from git_routes import create_git_router
from git_workspace import GitWorkspace, PagesTarget


class GitWorkspaceTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.configure(self.root)
        self.workspace = GitWorkspace(self.root)

    def git(self, *args, root=None, check=True):
        result = subprocess.run(["git", *args], cwd=root or self.root, capture_output=True,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if check and result.returncode:
            self.fail(result.stderr.decode("utf-8", errors="replace"))
        return result.stdout.decode("utf-8").strip()

    def configure(self, root):
        self.git("config", "user.name", "Git Test", root=root)
        self.git("config", "user.email", "git-test@example.test", root=root)
        self.git("config", "core.autocrlf", "false", root=root)
        self.git("config", "commit.gpgSign", "false", root=root)
        self.git("config", "core.hooksPath", str(self.directory / "unused-hooks"), root=root)

    def write(self, path, value, *, root=None):
        (root or self.root).joinpath(path).write_bytes(value.encode("utf-8"))

    def initial(self):
        self.write("keep.txt", "keep")
        self.write("edit.txt", "initial")
        self.git("add", "keep.txt", "edit.txt")
        self.git("commit", "-qm", "chore: 初始化")
        return self.git("rev-parse", "HEAD")

    def remote(self):
        bare = self.directory / "upstream.git"
        self.git("init", "-q", "--bare", "-b", "main", str(bare))
        self.git("remote", "add", "origin", str(bare))
        self.git("push", "-qu", "origin", "main")
        peer = self.directory / "peer"
        self.git("clone", "-q", str(bare), str(peer))
        self.configure(peer)
        return bare, peer

    def peer_commit(self, peer):
        self.write("remote.txt", "peer", root=peer)
        self.git("add", "remote.txt", root=peer)
        self.git("commit", "-qm", "feat: 更新远端", root=peer)
        self.git("push", "-q", root=peer)
        return self.git("rev-parse", "HEAD", root=peer)

    def assert_error(self, code, operation):
        with self.assertRaises(ContentError) as caught:
            operation()
        self.assertEqual(caught.exception.code, code)

    def commit_preview(self, *paths):
        return self.workspace.preview("commit", list(paths), "feat: 提交所选文件")

    def test_status_and_diff_distinguish_index_worktree_and_untracked(self):
        head = self.initial()
        self.write("edit.txt", "staged")
        self.git("add", "edit.txt")
        self.write("edit.txt", "working")
        self.write("新增 文档.md", "# 未跟踪\n")
        state = self.workspace.status()
        self.assertEqual((state["branch"], state["head"], state["upstream"]), ("main", head, None))
        self.assertEqual([(item["path"], item["staged"], item["unstaged"]) for item in state["changes"]],
                         [("edit.txt", "M", "M"), ("新增 文档.md", ".", "?")])
        diff = self.workspace.diff("edit.txt")
        self.assertIn("+staged", diff["staged"])
        self.assertIn("+working", diff["unstaged"])
        self.assertEqual(self.workspace.diff("新增 文档.md")["staged"], "")
        self.assertIn("+# 未跟踪", self.workspace.diff("新增 文档.md")["unstaged"])

    def test_first_commit_excludes_existing_index_and_unselected_files(self):
        self.write("other.txt", "already staged")
        self.git("add", "other.txt")
        self.write("新增 文档.md", "selected")
        self.write("unselected.txt", "untracked")
        self.assertIsNone(self.workspace.status()["head"])
        preview = self.commit_preview("新增 文档.md")
        result = self.workspace.execute(preview["token"])
        self.assertEqual(result["commit"], self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("ls-tree", "--name-only", "HEAD", "--", "other.txt"), "")
        self.assertEqual(self.git("show", "HEAD:新增 文档.md"), "selected")
        self.assertEqual(self.git("show", ":other.txt"), "already staged")
        self.assertTrue((self.root / "unselected.txt").is_file())

    def test_selected_commit_preserves_unrelated_partial_index_and_uses_literal_paths(self):
        base = self.initial()
        self.write("keep.txt", "preserve index")
        self.git("add", "keep.txt")
        self.write("keep.txt", "preserve disk")
        self.write("edit.txt", "selected index")
        self.git("add", "edit.txt")
        self.write("edit.txt", "selected disk")
        self.write("[a].txt", "literal")
        self.write("a.txt", "glob sibling")
        preview = self.commit_preview("edit.txt", "[a].txt")
        self.assertEqual(preview["paths"], ["edit.txt", "[a].txt"])
        self.assertIn("+selected disk", preview["patch"])
        self.assertNotIn("preserve", preview["patch"])
        self.workspace.execute(preview["token"])
        self.assertEqual(self.git("rev-parse", "HEAD^"), base)
        self.assertEqual(self.git("diff-tree", "-r", "--no-commit-id", "--name-only", "HEAD").splitlines(),
                         ["[a].txt", "edit.txt"])
        self.assertEqual(self.git("show", "HEAD:edit.txt"), "selected disk")
        self.assertEqual(self.git("show", ":keep.txt"), "preserve index")
        self.assertEqual((self.root / "keep.txt").read_text(), "preserve disk")
        self.assertEqual(self.git("status", "--short", "--", "edit.txt"), "")

    def test_selected_deletion_commits_only_the_named_file(self):
        self.initial()
        (self.root / "edit.txt").unlink()
        self.write("keep.txt", "unchanged by commit")
        preview = self.commit_preview("edit.txt")
        self.workspace.execute(preview["token"])
        self.assertEqual(self.git("diff-tree", "-r", "--no-commit-id", "--name-status", "HEAD"), "D\tedit.txt")
        self.assertEqual(self.git("status", "--short"), "M keep.txt")

    def test_same_status_new_bytes_invalidate_and_consume_commit_preview(self):
        head = self.initial()
        self.write("edit.txt", "seen")
        preview = self.commit_preview("edit.txt")
        self.write("edit.txt", "changed without altering status")
        self.assert_error("git_state_changed", lambda: self.workspace.execute(preview["token"]))
        self.assert_error("git_preview_expired", lambda: self.workspace.execute(preview["token"]))
        self.assertEqual(self.git("rev-parse", "HEAD"), head)

    def test_path_boundaries_and_stale_index_lock_prevent_mutation(self):
        head = self.initial()
        self.write("edit.txt", "changed")
        for path in ("../edit.txt", ".git/config", "C:/edit.txt", ".", "keep.txt"):
            with self.subTest(path=path):
                self.assert_error("git_invalid_path", lambda: self.workspace.diff(path))
        preview = self.commit_preview("edit.txt")
        (self.root / ".git" / "index.lock").touch()
        self.assert_error("git_busy", lambda: self.workspace.execute(preview["token"]))
        self.assertTrue((self.root / ".git" / "index.lock").exists())
        self.assertEqual(self.git("rev-parse", "HEAD"), head)

    def test_merge_conflict_is_visible_and_blocks_mutation(self):
        self.initial()
        self.git("branch", "other")
        self.write("edit.txt", "main")
        self.git("commit", "-qam", "feat: 主分支修改")
        self.git("switch", "-q", "other")
        self.write("edit.txt", "other")
        self.git("commit", "-qam", "feat: 其他分支修改")
        self.git("switch", "-q", "main")
        self.git("merge", "other", check=False)
        status = self.workspace.status()
        self.assertEqual(status["operation"], "merge")
        self.assertTrue(status["changes"][0]["conflicted"])
        self.assertFalse(status["changes"][0]["selectable"])
        self.assert_error("git_operation_in_progress", lambda: self.commit_preview("edit.txt"))

    def test_update_rejects_dirty_state_and_fast_forwards_clean_checkout(self):
        head = self.initial()
        _, peer = self.remote()
        target = self.peer_commit(peer)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        preview = self.workspace.preview("update")
        self.assertEqual(preview["target_commit"], target)
        self.write("untracked.txt", "keep")
        self.assert_error("git_dirty", lambda: self.workspace.execute(preview["token"]))
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        (self.root / "untracked.txt").unlink()
        preview = self.workspace.preview("update")
        self.workspace.execute(preview["token"])
        self.assertEqual(self.git("rev-parse", "HEAD"), target)
        self.assertEqual(self.git("rev-parse", "@{upstream}"), target)
        self.assertEqual((self.root / "remote.txt").read_text(), "peer")

    def test_update_and_push_refuse_divergence(self):
        self.initial()
        bare, peer = self.remote()
        remote_head = self.peer_commit(peer)
        self.write("edit.txt", "local")
        self.git("commit", "-qam", "feat: 更新本地")
        local_head = self.git("rev-parse", "HEAD")
        self.git("fetch", "-q", "origin")
        for action in ("update", "push"):
            with self.subTest(action=action):
                self.assert_error("git_diverged", lambda: self.workspace.preview(action))
        self.assertEqual(self.git("rev-parse", "HEAD"), local_head)
        self.assertEqual(self.git("rev-parse", "HEAD", root=bare), remote_head)

    def test_push_only_sends_reviewed_head_to_upstream(self):
        old = self.initial()
        bare, _ = self.remote()
        self.write("edit.txt", "push commit")
        self.git("commit", "-qam", "feat: 推送单个分支")
        head = self.git("rev-parse", "HEAD")
        self.git("tag", "local-tag")
        self.git("branch", "local-branch")
        self.git("config", "push.followTags", "true")
        self.write("keep.txt", "uncommitted")
        preview = self.workspace.preview("push")
        self.assertEqual(preview["target_commit"], head)
        self.assertEqual(preview["remote_head"], old)
        self.assertIn("upstream.git", preview["remote_address"])
        self.assertEqual(self.git("rev-parse", "HEAD", root=bare), old)
        self.workspace.execute(preview["token"])
        self.assertEqual(self.git("rev-parse", "HEAD", root=bare), head)
        self.assertEqual(self.git("for-each-ref", "--format=%(refname)", root=bare), "refs/heads/main")
        self.assertEqual(self.git("status", "--short"), "M keep.txt")

    def test_changed_remote_head_invalidates_push_confirmation(self):
        self.initial()
        bare, peer = self.remote()
        self.write("edit.txt", "local")
        self.git("commit", "-qam", "feat: 本地修改")
        preview = self.workspace.preview("push")
        target = self.peer_commit(peer)
        self.assert_error("git_state_changed", lambda: self.workspace.execute(preview["token"]))
        self.assertEqual(self.git("rev-parse", "HEAD", root=bare), target)

    def test_remote_operations_reject_upstream_mapped_to_a_local_branch(self):
        self.initial()
        _, peer = self.remote()
        self.git("branch", "local-backup")
        backup = self.git("rev-parse", "local-backup")
        self.peer_commit(peer)
        self.git("config", "remote.origin.fetch", "+refs/heads/main:refs/heads/local-backup")
        for action in ("update", "push"):
            with self.subTest(action=action):
                self.assert_error("git_upstream_required", lambda: self.workspace.preview(action))
        self.assertEqual(self.git("rev-parse", "local-backup"), backup)

    def test_publish_is_a_separate_confirmed_single_use_action(self):
        head = self.initial()
        self.remote()
        self.assert_error("git_publish_unconfigured", lambda: self.workspace.preview("publish"))
        self.git("remote", "set-url", "origin", "https://github.com/example/site.git")
        calls = []
        workspace = GitWorkspace(self.root, pages=PagesTarget("example/site", "main"), dispatch=calls.append)
        with patch.object(workspace, "_remote_head", return_value=head):
            preview = workspace.preview("publish")
            self.assertEqual(calls, [])
            self.assertEqual(preview["target"], "example/site · main · deploy.yml")
            workspace.execute(preview["token"])
            self.assertEqual(calls, [PagesTarget("example/site", "main")])
            self.assert_error("git_preview_expired", lambda: workspace.execute(preview["token"]))

    def test_router_requires_literal_confirmation_and_keeps_preview_usable(self):
        self.initial()
        self.write("edit.txt", "changed")
        app = FastAPI()
        app.include_router(create_git_router(self.root))

        @app.exception_handler(ContentError)
        async def content_error(_request: Request, error: ContentError):
            return JSONResponse({"code": error.code, "message": error.message}, status_code=error.status)

        client = TestClient(app)
        status = client.get("/api/v1/git/status")
        self.assertEqual(status.json()["changes"][0]["path"], "edit.txt")
        preview = client.post("/api/v1/git/preview", json={
            "action": "commit", "paths": ["edit.txt"], "message": "fix: 修正测试内容"
        })
        token = preview.json()["token"]
        self.assertEqual(client.post("/api/v1/git/execute", json={"token": token, "confirm": "true"}).status_code, 422)
        response = client.post("/api/v1/git/execute", json={"token": token, "confirm": False})
        self.assertEqual(response.json()["code"], "git_confirmation_required")
        response = client.post("/api/v1/git/execute", json={"token": token, "confirm": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["commit"], self.git("rev-parse", "HEAD"))
