"""Shared helpers for content workflows."""

from pathlib import Path


def restore_file_snapshot(path: Path, snapshot: str | None) -> None:
    """Restore a text file snapshot, deleting the file when the snapshot is None."""
    if snapshot is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot, encoding="utf-8")


class FileSnapshotRollback:
    """Record text file snapshots and restore them when a workflow fails."""

    def __init__(self) -> None:
        self._snapshots: list[tuple[Path, str | None]] = []

    def snapshot(self, path: Path | None) -> Path | None:
        """Capture the current file content; missing files are restored by deletion."""
        if path is None:
            return None
        snapshot = path.read_text(encoding="utf-8") if path.exists() else None
        self._snapshots.append((path, snapshot))
        return path

    def restore_all(self) -> None:
        """Restore snapshots in reverse registration order."""
        for path, snapshot in reversed(self._snapshots):
            restore_file_snapshot(path, snapshot)
