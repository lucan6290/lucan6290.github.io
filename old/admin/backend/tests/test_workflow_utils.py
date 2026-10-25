from pathlib import Path

from scr.application.content.workflows.utils import FileSnapshotRollback


def test_file_snapshot_rollback_restores_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "index.md"
    target.write_text("before", encoding="utf-8")
    rollback = FileSnapshotRollback()

    rollback.snapshot(target)
    target.write_text("after", encoding="utf-8")
    rollback.restore_all()

    assert target.read_text(encoding="utf-8") == "before"


def test_file_snapshot_rollback_deletes_file_created_after_snapshot(tmp_path: Path) -> None:
    target = tmp_path / "tags.yml"
    rollback = FileSnapshotRollback()

    rollback.snapshot(target)
    target.write_text("tags: []\n", encoding="utf-8")
    rollback.restore_all()

    assert not target.exists()
