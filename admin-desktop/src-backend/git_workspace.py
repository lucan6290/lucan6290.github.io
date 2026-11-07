"""Git 只操作桌面会话绑定的仓库，变更操作需要一次性预览。"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PureWindowsPath
import re
import secrets
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import RLock
import time
from typing import BinaryIO, Callable
from urllib.parse import urlsplit, urlunsplit

from content_store import ContentError


COMMIT_MESSAGE = re.compile(r"(feat|fix|docs|style|refactor|test|chore): [^\r\n]{1,30}")
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
GITHUB_REPO = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)
GITHUB_URL = re.compile(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+/[\w.-]+)")
OPERATION_MARKERS = (
    ("rebase-merge", "rebase"), ("rebase-apply", "rebase"), ("MERGE_HEAD", "merge"),
    ("CHERRY_PICK_HEAD", "cherry-pick"), ("REVERT_HEAD", "revert"), ("sequencer", "sequencer"),
    ("BISECT_START", "bisect"),
)
REPO_ENV = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX", "GIT_CONFIG",
    "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_GRAFT_FILE", "GIT_SHALLOW_FILE",
    "GIT_LITERAL_PATHSPECS", "GIT_GLOB_PATHSPECS", "GIT_NOGLOB_PATHSPECS", "GIT_ICASE_PATHSPECS",
}
DIFF_OPTIONS = ("--no-ext-diff", "--no-textconv", "--no-color", "--no-renames")
MAX_DIFF = 200_000


@dataclass(frozen=True)
class PagesTarget:
    repository: str
    branch: str

    @classmethod
    def from_environment(cls):
        repository = os.getenv("LUCHUAN_GITHUB_PAGES_REPO", "")
        branch = os.getenv("LUCHUAN_GITHUB_PAGES_BRANCH", "")
        if GITHUB_REPO.fullmatch(repository) and branch and not branch.startswith("-"):
            return cls(repository, branch)
        return None


@dataclass(frozen=True)
class RemoteTarget:
    remote: str
    ref: str
    tracking: str
    url: str

    @property
    def branch(self):
        return self.ref.removeprefix("refs/heads/")

    @property
    def label(self):
        return f"{self.remote}/{self.branch}"

    @property
    def display_address(self):
        if "://" in self.url:
            try:
                url = urlsplit(self.url)
                return urlunsplit((url.scheme, url.netloc.rsplit("@", 1)[-1], url.path, "", ""))
            except ValueError:
                return self.remote
        return re.sub(r"^[^/\\:]+@(?=[^/\\:]+:)", "", self.url)


@dataclass
class Preview:
    action: str
    branch: str
    head: str | None
    paths: list[str]
    message: str | None
    expires: float
    tree: str | None = None
    index_digest: bytes | None = None
    remote: RemoteTarget | None = None
    remote_head: str | None = None


@dataclass
class LockedIndex:
    original: Path
    path: Path
    file: BinaryIO
    installed: bool = False

    def prepare(self, source):
        self.file.write(source.read_bytes())
        self.file.flush()
        os.fsync(self.file.fileno())

    def install(self):
        self.file.close()
        os.replace(self.path, self.original)
        self.installed = True


def text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def stale():
    return ContentError(409, "git_state_changed", "Git 状态已变化，请刷新并重新预览")


class GitWorkspace:
    def __init__(self, project_root: Path, *, pages: PagesTarget | None = None,
                 dispatch: Callable[[PagesTarget], None] | None = None):
        self.root = project_root.resolve()
        self.pages = pages or PagesTarget.from_environment()
        self.dispatch = dispatch or self._dispatch_pages
        self.lock = RLock()
        self.previews: dict[str, Preview] = {}

    def _run(self, executable, args, *, input_data=None, index=None, timeout=20, configuration=None):
        program = shutil.which(f"{executable}.exe" if os.name == "nt" else executable)
        if not program:
            raise ContentError(503, "git_tool_unavailable", f"未找到本机 {executable}，请安装后重试")
        env = {key: value for key, value in os.environ.items() if key.upper() not in REPO_ENV}
        env.update(GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", GCM_INTERACTIVE="never",
                   GH_PROMPT_DISABLED="1", GH_NO_UPDATE_NOTIFIER="1", GIT_NO_REPLACE_OBJECTS="1",
                   GIT_ALLOW_PROTOCOL="file:https:ssh", GIT_NO_LAZY_FETCH="1", GIT_GRAFT_FILE=os.devnull)
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        if configuration:
            env["GIT_CONFIG_COUNT"] = str(len(configuration))
            for number, (key, value) in enumerate(configuration.items()):
                env[f"GIT_CONFIG_KEY_{number}"] = key
                env[f"GIT_CONFIG_VALUE_{number}"] = value
        try:
            stdin = subprocess.DEVNULL if input_data is None else None
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            return subprocess.run([program, *args], cwd=self.root, env=env, capture_output=True,
                                  input=input_data, stdin=stdin, timeout=timeout, shell=False, creationflags=flags)
        except subprocess.TimeoutExpired as error:
            raise ContentError(504, "git_timeout", "Git 操作超时，请先检查本地仓库或远端状态") from error
        except OSError as error:
            raise ContentError(503, "git_tool_unavailable", f"无法运行本机 {executable}") from error

    def _git(self, *args, allow=(0,), index=None, input_data=None, timeout=20, configuration=None,
             failure="Git 命令执行失败，请检查本机仓库和凭据"):
        result = self._run("git", ["--literal-pathspecs", "-c", "core.fsmonitor=false", *args],
                           index=index, input_data=input_data, timeout=timeout, configuration=configuration)
        if result.returncode not in allow:
            raise ContentError(409, "git_command_failed", failure)
        return result

    def _check_root(self):
        result = self._git("rev-parse", "--show-toplevel", allow=(0, 128))
        if result.returncode or Path(os.fsdecode(result.stdout.rstrip(b"\r\n"))).resolve() != self.root:
            raise ContentError(409, "git_repository_required", "当前内容库目录须为 Git 工作树根目录")

    def _oid(self, ref):
        result = self._git("rev-parse", "--verify", "--quiet", ref, allow=(0, 1))
        return text(result.stdout).strip() or None

    def _git_path(self, name):
        output = self._git("rev-parse", "--path-format=absolute", "--git-path", name).stdout
        return Path(os.fsdecode(output.rstrip(b"\r\n")))

    def _symbolic_ref(self, ref):
        result = self._git("symbolic-ref", "--quiet", "--no-recurse", ref, allow=(0, 1))
        return text(result.stdout).strip() or None

    def _valid_file(self, path):
        pieces = path.split("/")
        if (not path or "\0" in path or "\\" in path or PureWindowsPath(path).drive
                or any(part.lower() in {"", ".", "..", ".git"} for part in pieces)):
            return False
        try:
            target = self.root.joinpath(*pieces)
            return not target.is_dir() and target.resolve().is_relative_to(self.root)
        except (OSError, ValueError, RuntimeError):
            return False

    def _tracking(self, branch):
        if not branch:
            return None
        result = self._git("for-each-ref", "--format=%(refname)%00%(upstream:remotename)%00%(upstream:remoteref)%00%(upstream)",
                           f"refs/heads/{branch}").stdout
        for line in result.splitlines():
            ref, remote, upstream_ref, tracking = text(line).split("\0")
            if ref == f"refs/heads/{branch}" and remote and tracking and upstream_ref.startswith("refs/heads/"):
                return remote, upstream_ref, tracking
        return None

    def _status(self):
        raw = self._git("status", "--porcelain=v2", "-z", "--branch", "--no-renames",
                        "--ignore-submodules=none", "--untracked-files=all").stdout
        branch = head = None
        changes = []
        for entry in raw.split(b"\0"):
            if entry.startswith(b"# branch.head "):
                value = text(entry[14:])
                branch = None if value == "(detached)" else value
            elif entry.startswith(b"# branch.oid "):
                value = text(entry[13:])
                head = None if value == "(initial)" else value
            elif entry.startswith((b"1 ", b"u ", b"? ")):
                if entry.startswith(b"? "):
                    xy, submodule, name = b".?", b"N...", entry[2:]
                else:
                    fields = entry.split(b" ", 10 if entry.startswith(b"u ") else 8)
                    xy, submodule, name = fields[1], fields[2], fields[-1]
                path = text(name)
                conflict = entry.startswith(b"u ")
                changes.append({"path": path, "staged": chr(xy[0]), "unstaged": chr(xy[1]),
                                "conflicted": conflict, "selectable": not conflict and
                                not submodule.startswith(b"S") and path.encode("utf-8") == name and self._valid_file(path)})
        git_dir = self._git_path("HEAD").parent
        operation = next((name for marker, name in OPERATION_MARKERS if (git_dir / marker).exists()), None)
        tracking = self._tracking(branch)
        upstream = None
        if tracking:
            remote, ref, tracking_ref = tracking
            counts = None
            if head and self._oid(tracking_ref):
                counts = text(self._git("rev-list", "--left-right", "--count", f"{head}...{tracking_ref}").stdout).split()
            upstream = {"remote": remote, "branch": ref.removeprefix("refs/heads/"),
                        "ahead": int(counts[0]) if counts else None, "behind": int(counts[1]) if counts else None}
        return {"branch": branch, "head": head, "upstream": upstream, "operation": operation,
                "changes": changes, "publish_configured": self.pages is not None}

    def status(self):
        with self.lock:
            self._check_root()
            return self._status()

    def diff(self, path):
        with self.lock:
            self._check_root()
            item = next((item for item in self._status()["changes"] if item["path"] == path), None)
            if not item or not self._valid_file(path):
                raise ContentError(400, "git_invalid_path", "请选择 Git 变更列表中的仓库文件")
            if item["unstaged"] == "?":
                staged = b""
                unstaged = self._git("diff", "--no-index", *DIFF_OPTIONS, "--", "/dev/null", path,
                                     allow=(0, 1)).stdout
            else:
                staged = self._git("diff", "--cached", *DIFF_OPTIONS, "--", path).stdout
                unstaged = self._git("diff", *DIFF_OPTIONS, "--", path).stdout
            return {"path": path, "staged": text(staged[:MAX_DIFF]), "unstaged": text(unstaged[:MAX_DIFF]),
                    "truncated": len(staged) > MAX_DIFF or len(unstaged) > MAX_DIFF}

    def _eligible(self, action, state):
        if state["operation"] or any(item["conflicted"] for item in state["changes"]):
            raise ContentError(409, "git_operation_in_progress", "Git 正在进行其他操作或存在冲突，请先在仓库中处理")
        if not state["branch"] or (action != "commit" and not state["head"]):
            raise ContentError(409, "git_branch_required", "请先切换到可操作的本地分支")
        if action in {"update", "publish"} and state["changes"]:
            raise ContentError(409, "git_dirty", "工作区存在变更，请先处理暂存、未暂存和未跟踪文件")

    def _validate_selection(self, state, paths, message):
        if not message or not COMMIT_MESSAGE.fullmatch(message) or not re.search(r"[\u3400-\u9fff]", message):
            raise ContentError(400, "git_invalid_message", "请输入规范提交描述，例如 feat: 更新文章（描述不超过 30 字）")
        selectable = {item["path"] for item in state["changes"] if item["selectable"]}
        if not paths or len(paths) != len(set(paths)) or any(path not in selectable for path in paths):
            raise ContentError(400, "git_invalid_path", "请选择变更列表中可提交的文件，每个文件只选一次")

    def _snapshot(self, state, paths, index):
        head = state["head"]
        self._git("read-tree", head if head else "--empty", index=index)
        base = text(self._git("write-tree", index=index).stdout).strip()
        # NUL-delimited input avoids command-line length limits and keeps file names literal.
        self._git("add", "-A", "--pathspec-from-file=-", "--pathspec-file-nul", index=index,
                  input_data=self._path_input(paths))
        tree = text(self._git("write-tree", index=index).stdout).strip()
        changed = self._git("diff-tree", "-r", "--no-renames", "--name-only", "-z", base, tree).stdout
        if set(changed.split(b"\0")[:-1]) != {path.encode("utf-8") for path in paths}:
            raise ContentError(409, "git_selection_mismatch", "所选文件的工作区版本无法精确组成提交，请重新选择")
        return base, tree

    @staticmethod
    def _path_input(paths):
        return b"".join(path.encode("utf-8") + b"\0" for path in paths)

    @staticmethod
    def _index_digest(index_path):
        return hashlib.sha256(index_path.read_bytes() if index_path.exists() else b"").digest()

    def _remote_target(self, branch, action):
        tracking = self._tracking(branch)
        if not tracking or tracking[0] == "." or not tracking[2].startswith("refs/remotes/"):
            raise ContentError(409, "git_upstream_required", "当前分支须先配置远程上游分支")
        remote, ref, tracking_ref = tracking
        if self._symbolic_ref(tracking_ref):
            raise ContentError(409, "git_upstream_required", "远程跟踪引用必须直接指向提交")
        options = ("--push",) if action == "push" else ()
        urls = self._git("remote", "get-url", "--all", *options, "--", remote).stdout.splitlines()
        if len(urls) != 1:
            raise ContentError(409, "git_remote_ambiguous", "请为上游配置唯一的远程地址")
        if action == "push":
            mirror = self._git("config", "--type=bool", "--get", f"remote.{remote}.mirror", allow=(0, 1))
            if mirror.stdout.strip() == b"true":
                raise ContentError(409, "git_remote_ambiguous", "镜像远端不支持单分支安全推送")
        url = text(urls[0])
        if not url or url.encode("utf-8") != urls[0]:
            raise ContentError(409, "git_remote_ambiguous", "远程地址无效")
        return RemoteTarget(remote, ref, tracking_ref, url)

    def _pinned_remote(self, target, command, *options, refs, **kwargs):
        nonce = secrets.token_hex(16)
        remote = f"luchuan-{nonce}"
        marker = f"luchuan-pin:{nonce}"
        # Git rewrites this unique URL once. Explicit pushurl suppresses pushInsteadOf.
        configuration = {
            f"remote.{remote}.url": marker,
            f"remote.{remote}.pushurl": marker,
            f"url.{target.url}.insteadOf": marker,
            "http.followRedirects": "false",
        }
        if target.url.lower().startswith("https://"):
            configuration[f"http.{target.url}.followRedirects"] = "false"
        return self._git(command, *options, "--", remote, *refs, configuration=configuration, **kwargs)

    def _remote_head(self, target):
        result = self._pinned_remote(target, "ls-remote", "--exit-code", "--refs", refs=(target.ref,),
                                     allow=(0, 2), timeout=35, failure="查询远端失败，请检查网络和本机 Git 凭据")
        oid, _, ref = text(result.stdout).strip().partition("\t")
        if not OID.fullmatch(oid) or ref != target.ref:
            raise ContentError(409, "git_remote_branch_missing", "远端找不到配置的上游分支")
        return oid

    def _check_direction(self, action, head, remote_head, *, fetched=False):
        if head == remote_head:
            return
        if not fetched and not self._oid(f"{remote_head}^{{commit}}"):
            if action == "update":
                return
            raise ContentError(409, "git_remote_unknown", "远端有未知提交，请先更新或在本机检查分支关系")
        old, new = (head, remote_head) if action == "update" else (remote_head, head)
        if self._git("merge-base", "--is-ancestor", old, new, allow=(0, 1)).returncode:
            raise ContentError(409, "git_diverged", "本地与远端无法按当前操作快进，请检查分支关系")

    def _publish_target(self, state, target):
        pages = self.pages
        match = GITHUB_URL.fullmatch(target.url) if target else None
        if (not pages or not match or match[1].removesuffix(".git").casefold() != pages.repository.casefold()
                or pages.branch != target.branch or pages.branch != state["branch"]):
            raise ContentError(409, "git_publish_unconfigured", "当前分支与配置的 GitHub Pages 仓库及发布分支不一致")
        return f"{pages.repository} · {pages.branch} · deploy.yml"

    def preview(self, action, paths=None, message=None):
        paths = list(paths or [])
        with self.lock:
            self._check_root()
            state = self._status()
            if action == "publish" and not self.pages:
                raise ContentError(409, "git_publish_unconfigured", "请先配置 GitHub Pages 发布仓库和分支")
            self._eligible(action, state)
            plan = Preview(action, state["branch"], state["head"], paths, message, time.monotonic() + 300)
            target_label = plan.branch
            target_commit = None
            patch = b""
            if action == "commit":
                self._validate_selection(state, paths, message)
                real_index = self._git_path("index")
                plan.index_digest = self._index_digest(real_index)
                with TemporaryDirectory(prefix="luchuan-git-") as temporary:
                    base, plan.tree = self._snapshot(state, paths, Path(temporary) / "index")
                patch = self._git("diff-tree", "-r", "-p", *DIFF_OPTIONS, base, plan.tree).stdout
            else:
                if paths or message is not None:
                    raise ContentError(400, "git_invalid_scope", "远端操作只使用已配置的上游，不能指定文件或提交描述")
                target = self._remote_target(plan.branch, action)
                target_label = self._publish_target(state, target) if action == "publish" else target.label
                plan.remote = target
                plan.remote_head = self._remote_head(target)
                if action == "publish":
                    if plan.head != plan.remote_head:
                        raise ContentError(409, "git_publish_unsynced", "本地与发布分支提交不同，请先确认并同步")
                else:
                    self._check_direction(action, plan.head, plan.remote_head)
                target_commit = plan.remote_head if action == "update" else plan.head
            self.previews = {key: value for key, value in self.previews.items() if value.expires > time.monotonic()}
            if len(self.previews) >= 24:
                self.previews.pop(next(iter(self.previews)))
            token = secrets.token_urlsafe(24)
            self.previews[token] = plan
            return {"token": token, "action": action, "branch": plan.branch, "head": plan.head, "target": target_label,
                    "target_commit": target_commit, "paths": paths, "message": message,
                    "remote_head": plan.remote_head, "remote_address": plan.remote.display_address if plan.remote else None,
                    "patch": text(patch[:MAX_DIFF]), "truncated": len(patch) > MAX_DIFF}

    @contextmanager
    def _index_lock(self):
        index_path = self._git_path("index")
        lock_path = index_path.with_name(index_path.name + ".lock")
        try:
            locked = LockedIndex(index_path, lock_path, lock_path.open("xb"))
        except FileExistsError as error:
            raise ContentError(409, "git_busy", "Git 索引正在使用，请稍后重新预览") from error
        except OSError as error:
            raise ContentError(409, "git_index_failed", "无法锁定本机 Git 索引") from error
        try:
            yield locked
        finally:
            locked.file.close()
            # After a successful replace the lock name belongs to the next Git writer.
            if not locked.installed:
                lock_path.unlink(missing_ok=True)

    def _commit(self, plan):
        with self._index_lock() as locked:
            return self._commit_locked(plan, locked)

    def _commit_locked(self, plan, locked):
        try:
            state = self._status()
            self._check_local(plan, state)
            if self._index_digest(locked.original) != plan.index_digest:
                raise stale()
            with TemporaryDirectory(prefix="luchuan-git-") as temporary:
                snapshot = Path(temporary) / "snapshot"
                prepared = Path(temporary) / "index"
                self._validate_selection(state, plan.paths, plan.message)
                _, current_tree = self._snapshot(state, plan.paths, snapshot)
                if current_tree != plan.tree:
                    raise stale()
                if locked.original.exists():
                    shutil.copyfile(locked.original, prepared)
                else:
                    self._git("read-tree", "--empty", index=prepared)
                self._git("update-index", "--force-remove", "-z", "--stdin", index=prepared,
                          input_data=self._path_input(plan.paths))
                entries = self._git("ls-files", "--stage", "-z", index=snapshot).stdout
                selected = {path.encode("utf-8") for path in plan.paths}
                entries = b"".join(entry + b"\0" for entry in entries.split(b"\0")
                                   if entry.partition(b"\t")[2] in selected)
                self._git("update-index", "-z", "--index-info", index=prepared, input_data=entries)
                locked.prepare(prepared)

            options = ["-p", plan.head] if plan.head else []
            signing = self._git("config", "--type=bool", "--get", "commit.gpgSign", allow=(0, 1))
            if signing.stdout.strip() == b"true":
                options.append("-S")
            commit = text(self._git("-c", "i18n.commitEncoding=UTF-8", "commit-tree", plan.tree, *options,
                                    "-F", "-", input_data=(plan.message + "\n").encode("utf-8"),
                                    failure="无法创建提交，请检查 Git 用户名、邮箱和签名配置").stdout).strip()
            self._check_local(plan, self._status())
            ref = f"refs/heads/{plan.branch}"
            expected = plan.head or "0" * len(commit)
            self._git("update-ref", "--no-deref", "-m", f"commit: {plan.message}", ref, commit, expected,
                      failure="分支已变化，请重新预览")
            try:
                locked.install()
            except OSError as error:
                rollback = (ref, plan.head, commit) if plan.head else ("-d", ref, commit)
                try:
                    self._git("update-ref", "--no-deref", *rollback)
                except ContentError as rollback_error:
                    raise ContentError(409, "git_index_failed", "分支已提交但索引更新失败，请在本机检查 Git 状态") from rollback_error
                raise ContentError(409, "git_index_failed", "索引更新失败，已还原分支位置") from error
            return commit
        except OSError as error:
            raise ContentError(409, "git_index_failed", "无法准备 Git 索引，请检查仓库权限") from error

    def _check_local(self, plan, state):
        if (state["branch"], state["head"]) != (plan.branch, plan.head):
            raise stale()
        self._eligible(plan.action, state)

    def _update(self, plan, target):
        previous = self._oid(target.tracking)
        if plan.head == plan.remote_head:
            return self._sync_tracking(plan, target, previous, plan.remote_head, "本地分支已是最新")
        self._pinned_remote(target, "fetch", "--no-tags", "--no-recurse-submodules", "--no-write-fetch-head",
                            "--refmap=", refs=(plan.remote_head,), timeout=45, failure="获取已预览的远端提交失败")
        self._check_direction("update", plan.head, plan.remote_head, fetched=True)
        with self._index_lock() as locked, TemporaryDirectory(prefix="luchuan-git-") as temporary:
            self._check_local(plan, self._status())
            self._fast_forward(plan, locked, Path(temporary) / "index")
        return self._sync_tracking(plan, target, previous, plan.remote_head, "已快进更新本地分支")

    def _fast_forward(self, plan, locked, prepared):
        ref = f"refs/heads/{plan.branch}"
        if self._symbolic_ref("HEAD") != ref or self._symbolic_ref(ref):
            raise stale()
        checkout = ("-c", "submodule.recurse=false", "read-tree", "-m", "-u")
        try:
            if locked.original.exists():
                shutil.copyfile(locked.original, prepared)
            else:
                self._git("read-tree", plan.head, index=prepared)
        except OSError as error:
            raise ContentError(409, "git_index_failed", "无法准备 Git 索引，请检查仓库权限") from error
        self._git(*checkout, plan.head, plan.remote_head, index=prepared,
                  failure="快进更新失败，请检查是否有会被覆盖的文件")
        advanced = False
        try:
            locked.prepare(prepared)
            if self._symbolic_ref("HEAD") != ref or self._symbolic_ref(ref):
                raise stale()
            self._git("update-ref", "--no-deref", "-m", "luchuan: fast-forward",
                      ref, plan.remote_head, plan.head, failure="当前分支已变化，请重新预览")
            advanced = True
            locked.install()
        except (OSError, ContentError) as error:
            try:
                self._git(*checkout, plan.remote_head, plan.head, index=prepared)
                if advanced:
                    self._git("update-ref", "--no-deref", ref, plan.head, plan.remote_head)
            except ContentError as rollback_error:
                raise ContentError(409, "git_index_failed", "快进中断，请在本机检查工作区及分支状态") from rollback_error
            if isinstance(error, ContentError):
                raise
            raise ContentError(409, "git_index_failed", "索引更新失败，已还原工作区及分支位置") from error

    def _sync_tracking(self, plan, target, previous, commit, message):
        if previous == commit:
            return message
        try:
            if self._remote_target(plan.branch, plan.action) != target:
                raise stale()
            self._git("update-ref", "--no-deref", target.tracking, commit, previous or "0" * len(commit))
        except ContentError:
            return message + "，远端跟踪引用发生变化，请刷新后核对分支状态"
        return message

    def _dispatch_pages(self, pages):
        result = self._run("gh", ["workflow", "run", "deploy.yml", "--repo", f"github.com/{pages.repository}",
                                  "--ref", pages.branch], timeout=45)
        if result.returncode:
            raise ContentError(409, "git_publish_failed", "GitHub 未确认发布请求，请检查本机 gh 登录、权限和工作流")

    def execute(self, token):
        with self.lock:
            plan = self.previews.pop(token, None)
            if not plan or plan.expires <= time.monotonic():
                raise ContentError(409, "git_preview_expired", "预览已失效，请重新预览后确认")
            self._check_root()
            state = self._status()
            self._check_local(plan, state)
            commit = plan.head
            if plan.action == "commit":
                commit = self._commit(plan)
                message = "已创建所选文件的本地提交"
            else:
                target = self._remote_target(plan.branch, plan.action)
                if target != plan.remote or self._remote_head(target) != plan.remote_head:
                    raise stale()
                self._check_local(plan, self._status())
                if plan.action == "update":
                    message = self._update(plan, target)
                    commit = plan.remote_head
                elif plan.action == "push":
                    previous = self._oid(target.tracking)
                    self._check_direction("push", plan.head, plan.remote_head)
                    if plan.head != plan.remote_head:
                        self._pinned_remote(target, "push", "--no-follow-tags", "--recurse-submodules=no",
                                            f"--force-with-lease={target.ref}:{plan.remote_head}",
                                            refs=(f"{plan.head}:{target.ref}",), timeout=45,
                                            failure="推送失败，请检查分支状态、本机凭据与远端权限")
                    message = "远端已包含该提交" if plan.head == plan.remote_head else "已推送所确认的提交"
                    message = self._sync_tracking(plan, target, previous, plan.head, message)
                else:
                    self._publish_target(state, target)
                    self.dispatch(self.pages)
                    message = "GitHub 已接收发布请求，部署进度可在 Actions 查看"
            return {"action": plan.action, "message": message, "commit": commit}
