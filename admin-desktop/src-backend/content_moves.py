"""Versioned content moves, link repairs and graph lookup."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import tempfile

from content_mutations import document_snapshots, mutable_path, plan_digest
from content_store import ContentError, RESOURCE_DIRECTORY
from markdown_links import (decoded_parts, destinations, document_route, relative_reference, resolve_reference,
                            rewrite_destinations, route_reference, split_reference)
from media_library import image_directory, image_owner


@dataclass(frozen=True)
class Relocation:
    source: str
    destination: str
    signature: list[tuple[str, str | None]]


@dataclass(frozen=True)
class Rewrite:
    source: str
    destination: str
    original: bytes
    updated: bytes


def moved_path(path, moves):
    for move in moves:
        if path == move.source or path.startswith(move.source + "/"):
            return move.destination + path[len(move.source):]
    return path


def absolute_route(value):
    path, suffix = split_reference(value)
    if not path.startswith("/") or path.startswith("//"):
        return None
    parts = decoded_parts(path)
    if parts is None or any(part in {".", ".."} for part in parts):
        return None
    return ("/".join(parts).rstrip("/") or "/", suffix)


def tree_signature(root):
    signature = []
    pending = [root]
    while pending:
        path = pending.pop()
        if path.resolve() != path or path.is_symlink():
            raise ContentError(400, "invalid_path", "移动范围含符号链接或目录联接")
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            signature.append((relative, None))
            pending.extend(sorted(path.iterdir(), reverse=True))
        elif path.is_file():
            with path.open("rb") as stream:
                before = os.fstat(stream.fileno())
                digest = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
                after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ContentError(409, "stale_plan", "移动范围内有文件正在变化")
            signature.append((relative, digest.hexdigest()))
        else:
            raise ContentError(409, "stale_plan", "移动范围内有文件已变化或不是普通文件")
    return signature


def destination_exists(path):
    return any(item.name.casefold() == path.name.casefold() for item in path.parent.iterdir())


def relocate(source, target):
    if destination_exists(target):
        raise ContentError(409, "already_exists", "目标已有同名文件或目录")
    if os.name == "nt" or source.is_dir():
        os.rename(source, target)
        return
    # On POSIX link the inode first, so a concurrently created file is never replaced.
    os.link(source, target)
    try:
        source.unlink()
    except OSError:
        if target.samefile(source):
            target.unlink()
        raise


def replace_version(path, old, new):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".desktop-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(new)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != old:
            raise ContentError(409, "stale_plan", "待改写的文档已变化")
        os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class ContentMoves:
    def __init__(self, store):
        self.store = store

    def path(self, relative):
        return mutable_path(self.store, relative, directory=True)

    def relocation(self, source, destination):
        origin, target = self.path(source), self.path(destination)
        if not target.parent.is_dir():
            raise ContentError(404, "not_found", "目标的父目录不存在")
        if destination_exists(target):
            raise ContentError(409, "already_exists", "目标已有同名文件或目录")
        return Relocation(source, destination, tree_signature(origin))

    def prepare(self, source, destination, kind):
        if kind not in {"document", "directory"}:
            raise ContentError(400, "invalid_request", "移动类型必须是 document 或 directory")
        directory = kind == "directory"
        origin = mutable_path(self.store, source, directory=directory)
        mutable_path(self.store, destination, directory=directory)
        if not (origin.is_dir() if directory else origin.is_file()):
            raise ContentError(404, "not_found", "移动源已不存在")
        if directory and destination.casefold().startswith(source.casefold() + "/"):
            raise ContentError(400, "invalid_path", "不能把目录移动到自己的下级")
        parent_parts = destination.split("/") if directory else destination.split("/")[:-1]
        if any(RESOURCE_DIRECTORY.fullmatch(part) for part in parent_parts):
            raise ContentError(400, "invalid_path", "文档或分类不能移动到保留的资源目录")
        moves = [self.relocation(source, destination)]
        if not directory:
            media_source = image_directory(source)
            if self.path(media_source).exists():
                if not self.path(media_source).is_dir():
                    raise ContentError(409, "already_exists", "源配图目录被同名文件占用")
                image_owner(self.path(media_source))
                moves.append(self.relocation(media_source, image_directory(destination)))
            elif self.path(image_directory(destination)).exists():
                raise ContentError(409, "already_exists", "目标配图目录已存在")
        index = self.store.list_content()
        snapshots = dict(document_snapshots(self.store, index))
        directories = {item["relative_path"] for item in index["directories"] if item["relative_path"]}
        if source not in (directories if directory else snapshots):
            raise ContentError(400, "invalid_path", "移动源不属于可发布的文档目录")

        routes = {}
        for old in sorted(directories):
            new = moved_path(old, moves)
            if old != new:
                routes["/" + old] = "/" + new
        for old in sorted(snapshots):
            new = moved_path(old, moves)
            old_route, new_route = document_route(old), document_route(new)
            if old_route != new_route:
                routes[old_route] = new_route

        unchanged_routes = {"/" + old for old in directories if moved_path(old, moves) == old}
        # A category and its README share their public URL.
        unchanged_routes.update(document_route(old) for old in snapshots if moved_path(old, moves) == old)
        for old_route, new_route in routes.items():
            if new_route in unchanged_routes or new_route in {"/", "/about", "/series"}:
                # Moving README between categories intentionally changes their introduction.
                if not (not directory
                        and PurePosixPath(destination).name.lower() == "readme.md"
                        and new_route in {"/" + old for old in directories}):
                    raise ContentError(409, "route_conflict", "目标与已有博客 URL 冲突", {"route": new_route})

        changes_absolute_routes = directory or PurePosixPath(source).name.lower() != 'readme.md'
        rewrites = []
        for old, data in sorted(snapshots.items()):
            new = moved_path(old, moves)

            def replacement(value):
                absolute = absolute_route(value)
                if changes_absolute_routes and absolute and absolute[0] in routes:
                    trailing = "/" if split_reference(value)[0].endswith("/") and routes[absolute[0]] != "/" else ""
                    return route_reference(routes[absolute[0]]) + trailing + absolute[1]
                reference = resolve_reference(old, value)
                if not reference:
                    return None
                target, suffix = reference
                destination = moved_path(target, moves)
                if resolve_reference(new, value) == (destination, suffix):
                    return None
                return relative_reference(new, destination) + suffix

            updated = rewrite_destinations(data, replacement)
            if updated != data:
                rewrites.append(Rewrite(old, new, data, updated))

        files = {}
        for move in moves:
            for relative, version in move.signature:
                if version is not None:
                    tail = "" if relative == "." else "/" + relative
                    old, new = move.source + tail, move.destination + tail
                    files[old] = {"before": old, "after": new, "rewritten": False}
        for rewrite in rewrites:
            files[rewrite.source] = {"before": rewrite.source, "after": rewrite.destination, "rewritten": True}

        payload = {
            "source": source, "destination": destination, "kind": kind,
            "moves": [{"before": move.source, "after": move.destination} for move in moves],
            "files": [files[path] for path in sorted(files)],
            "routes": [{"before": before, "after": routes[before]} for before in sorted(routes)],
            "plan_id": plan_digest([
                kind, [(move.source, move.destination, move.signature) for move in moves],
                [(write.source, write.destination, self.store.version_of(write.original)) for write in rewrites],
                sorted(routes.items()),
            ]),
        }
        return payload, moves, rewrites

    def plan(self, source, destination, kind):
        with self.store.lock:
            try:
                return self.prepare(source, destination, kind)[0]
            except OSError as error:
                raise ContentError(409, "stale_plan", "移动范围暂不可读取，请重新检查") from error

    def apply(self, source, destination, kind, plan_id):
        with self.store.lock:
            try:
                payload, moves, rewrites = self.prepare(source, destination, kind)
            except OSError as error:
                raise ContentError(409, "stale_plan", "移动范围暂不可读取，请重新检查") from error
            if payload["plan_id"] != plan_id:
                raise ContentError(409, "stale_plan", "受影响文件已改变，请重新查看移动计划")
            moved, written = [], []
            try:
                for move in moves:
                    original = self.path(move.source)
                    if tree_signature(original) != move.signature:
                        raise ContentError(409, "stale_plan", "移动范围内文件已改变")
                    relocate(original, self.path(move.destination))
                    moved.append(move)
                for rewrite in rewrites:
                    replace_version(self.path(rewrite.destination), rewrite.original, rewrite.updated)
                    written.append(rewrite)
            except (OSError, ContentError) as error:
                failed = self.rollback(moved, written)
                if failed:
                    raise ContentError(500, "rollback_failed", "移动中断，部分路径需人工核对",
                                       {"paths": failed}) from error
                if isinstance(error, ContentError):
                    raise
                raise ContentError(500, "move_failed", "移动失败，原文件与链接已恢复") from error
            return payload

    def rollback(self, moves, rewrites):
        failed = []
        for rewrite in reversed(rewrites):
            try:
                replace_version(self.path(rewrite.destination), rewrite.updated, rewrite.original)
            except (OSError, ContentError):
                failed.append(rewrite.destination)
        for move in reversed(moves):
            try:
                destination = self.path(move.destination)
                if tree_signature(destination) != move.signature:
                    raise ContentError(409, "stale_plan", "回滚期间发现外部修改")
                relocate(destination, self.path(move.source))
            except (OSError, ContentError):
                failed.append(move.destination)
        return failed

    def graph(self):
        with self.store.lock:
            snapshots = dict(document_snapshots(self.store))
            by_route = {document_route(path): path for path in snapshots}
            edges = set()
            for source, data in snapshots.items():
                for span in destinations(data):
                    relative = resolve_reference(source, span.value)
                    absolute = absolute_route(span.value)
                    target = relative[0] if relative else by_route.get(absolute[0]) if absolute else None
                    if target and target != source and target in snapshots:
                        edges.add((source, target))
            return {"documents": sorted(snapshots),
                    "edges": [{"source": source, "target": target} for source, target in sorted(edges)]}
