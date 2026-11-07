"""Shared safeguards for compound content operations."""

import hashlib
import json

from content_store import ContentError


def mutable_path(store, relative_path, *, directory=False):
    target = store.path(relative_path, directory=directory)
    if target.resolve() != target or target.is_symlink():
        raise ContentError(400, "invalid_path", "写入路径不能穿过符号链接或目录联接")
    return target


def plan_digest(data):
    serial = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def document_snapshots(store):
    for document in store.list_content()["documents"]:
        relative_path = document["relative_path"]
        target = mutable_path(store, relative_path)
        data, _, _ = store.snapshot(target)
        yield relative_path, data
