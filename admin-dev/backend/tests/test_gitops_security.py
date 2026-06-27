from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from blog_admin.core.command_policy import CommandResult, GitCommandPolicy
from blog_admin.core.errors import CommandRejectedError
from blog_admin.modules.gitops.audit import GitAuditLogger
from blog_admin.modules.gitops.schemas import GitCommitRequest
from blog_admin.modules.gitops.service import GitCommandRunner, GitOpsService


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def run(self, *args: str) -> CommandResult:
        self.calls.append(tuple(args))
        return CommandResult(stdout="ok", stderr="")


def test_git_policy_rejects_unapproved_command_shapes(tmp_path: Path) -> None:
    policy = GitCommandPolicy(tmp_path)

    with pytest.raises(CommandRejectedError):
        policy.validate_args(("status",))
    with pytest.raises(CommandRejectedError):
        policy.validate_args(("push", "--force"))
    with pytest.raises(CommandRejectedError):
        policy.validate_args(("commit", "--amend"))


def test_git_policy_rejects_unsafe_add_targets(tmp_path: Path) -> None:
    policy = GitCommandPolicy(tmp_path)

    with pytest.raises(CommandRejectedError):
        policy.validate_add_target("../outside.md")
    with pytest.raises(CommandRejectedError):
        policy.validate_add_target(str(tmp_path / "outside.md"))
    with pytest.raises(CommandRejectedError):
        policy.validate_add_target(".")


def test_git_policy_allows_relative_add_target_inside_repo(tmp_path: Path) -> None:
    policy = GitCommandPolicy(tmp_path)
    target = tmp_path / "admin-dev" / "backend" / "main.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('ok')\n", encoding="utf-8")

    assert policy.validate_add_target("admin-dev/backend/main.py") == "admin-dev/backend/main.py"


def test_git_service_commit_uses_policy_checked_runner_sequence(tmp_path: Path) -> None:
    runner = FakeRunner()
    service = GitOpsService(tmp_path, runner=runner)
    target = tmp_path / "README.md"
    target.write_text("demo", encoding="utf-8")

    result = asyncio.run(service.commit(GitCommitRequest(message="提交说明", filePath="README.md")))

    assert result == {"stdout": "ok", "stderr": ""}
    assert runner.calls == [("add", "README.md"), ("commit", "-m", "提交说明")]


def test_git_service_deploy_adds_commits_and_pushes(tmp_path: Path) -> None:
    runner = FakeRunner()
    service = GitOpsService(tmp_path, runner=runner)

    result = asyncio.run(service.deploy(GitCommitRequest(message="部署", filePath=None)))

    assert result == {
        "commit": {"stdout": "ok", "stderr": ""},
        "push": {"stdout": "ok", "stderr": ""},
    }
    assert runner.calls == [("add", "."), ("commit", "-m", "部署"), ("push", "origin")]


def test_git_audit_logger_writes_jsonl_events(tmp_path: Path) -> None:
    audit_log = tmp_path / ".cache" / "gitops-audit.jsonl"
    logger = GitAuditLogger(audit_log)

    logger.record(
        action="git",
        args=("commit", "-m", "提交说明"),
        status="succeeded",
        details={"stdout": "ok"},
    )

    event = json.loads(audit_log.read_text(encoding="utf-8").strip())
    assert event["action"] == "git"
    assert event["args"] == ["commit", "-m", "提交说明"]
    assert event["status"] == "succeeded"
    assert event["details"] == {"stdout": "ok"}
    assert "timestamp" in event


def test_git_runner_audits_rejected_commands_without_spawning_process(tmp_path: Path) -> None:
    audit_log = tmp_path / ".cache" / "gitops-audit.jsonl"
    runner = GitCommandRunner(tmp_path, audit_logger=GitAuditLogger(audit_log))

    with pytest.raises(CommandRejectedError):
        asyncio.run(runner.run("status"))

    event = json.loads(audit_log.read_text(encoding="utf-8").strip())
    assert event["args"] == ["status"]
    assert event["status"] == "rejected"
    assert event["details"]["code"] == "COMMAND_REJECTED"
