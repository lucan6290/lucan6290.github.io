"""以 Markdown 原始字节为事实源的本地内容仓库。"""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import tempfile
import threading

import yaml

from article_frontmatter import ArticleError, FIELDS, exempt, maintain_updated, validate

MD_EXTENSIONS = {".md", ".mdx"}
NUMERIC_PREFIX = re.compile(r"^(\d+)[-_]")
RESOURCE_DIRECTORY = re.compile(r"^(?:images|assets|.*-imgs)$", re.IGNORECASE)
RESERVED_NAME = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.IGNORECASE)


class ContentError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def strip_prefix(name):
    return NUMERIC_PREFIX.sub("", name)


def sort_key(name):
    match = NUMERIC_PREFIX.match(name)
    return (0, match[1].zfill(6)) if match else (1, name.casefold())


def parse_markdown(raw):
    text = raw.removeprefix("\ufeff")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        raise ContentError(400, "invalid_yaml", "Front Matter 缺少结束分隔符", {"line": 1})
    try:
        metadata = yaml.safe_load("".join(lines[1:closing]))
    except (yaml.YAMLError, ValueError) as error:
        mark = getattr(error, "problem_mark", None)
        details = {"line": mark.line + 2, "column": mark.column + 1} if mark else {"line": 1}
        raise ContentError(400, "invalid_yaml", "Front Matter YAML 无效", details) from error
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ContentError(400, "invalid_yaml", "Front Matter 必须是 YAML 对象", {"line": 2})
    return metadata, "".join(lines[closing + 1:])


def first_heading(body):
    without_code = re.sub(r"^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?^ {0,3}\1[^\n]*$", "", body, flags=re.MULTILINE)
    match = re.search(r"^ {0,3}#[\t ]+(.+)$", without_code, flags=re.MULTILINE)
    return re.sub(r"[\t ]+#+[\t ]*$", "", match[1]).strip() if match else None


class ContentStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.content_root = (self.project_root / "frontend/content").resolve()
        if not self.content_root.is_dir() or not (self.project_root / "admin-desktop").is_dir():
            raise RuntimeError("项目根必须包含 frontend/content 与 admin-desktop")
        self.lock = threading.RLock()

    def path(self, relative_path, *, directory=False):
        if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path:
            raise ContentError(400, "invalid_path", "必须使用 / 分隔的安全相对路径")
        parts = relative_path.split("/")
        for part in parts:
            if (not part or part.startswith((".", "_")) or part.endswith((".", " "))
                    or re.search(r'[<>:"|?*\x00-\x1f]', part) or RESERVED_NAME.match(part)):
                raise ContentError(400, "invalid_path", "路径包含非法或保留名称")
        target = self.content_root.joinpath(*parts)
        try:
            target.resolve().relative_to(self.content_root)
        except (ValueError, OSError, RuntimeError) as error:
            raise ContentError(400, "invalid_path", "路径超出内容根或无法解析") from error
        if not directory and target.suffix.lower() not in MD_EXTENSIONS:
            raise ContentError(400, "invalid_path", "只允许 Markdown 文件")
        return target

    @staticmethod
    def version_of(data):
        return hashlib.sha256(data).hexdigest()

    def snapshot(self, target, *, tolerate_encoding=False):
        if target.is_dir():
            raise ContentError(400, "invalid_path", "目标是目录，不能作为文档")
        try:
            for _ in range(3):
                with target.open("rb") as source:
                    before = os.fstat(source.fileno())
                    data = source.read()
                    stat = os.fstat(source.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns):
                    break
            else:
                raise ContentError(409, "content_changing", "文档正在被外部写入，请稍后重试")
        except FileNotFoundError as error:
            raise ContentError(404, "not_found", "文档或父目录不存在") from error
        except IsADirectoryError as error:
            raise ContentError(400, "invalid_path", "目标是目录，不能作为文档") from error
        except OSError as error:
            raise ContentError(500, "read_failed", "无法读取文档") from error
        try:
            raw = data.decode("utf-8", errors="replace" if tolerate_encoding else "strict")
        except UnicodeDecodeError as error:
            raise ContentError(400, "invalid_encoding", "文档必须使用 UTF-8 编码") from error
        return data, raw, stat

    def detail(self, relative_path, *, summary=False):
        target = self.path(relative_path)
        data, raw, stat = self.snapshot(target, tolerate_encoding=summary)
        try:
            fm, body = parse_markdown(raw)
        except ContentError:
            if not summary:
                raise
            # 暂时无效的单篇文档仍出现在列表；详情接口负责返回定位错误。
            fm, body = {}, raw
        title = fm.get("title") or first_heading(body) or strip_prefix(target.stem)
        return {
            "relative_path": relative_path, "name": target.name, "title": str(title),
            "section": relative_path.split("/")[0] if "/" in relative_path else "",
            "kind": "introduction" if target.name.lower() == "readme.md" else "article",
            "tags": [str(tag) for tag in fm["tags"]] if isinstance(fm.get("tags"), list) else [],
            "description": str(fm.get("description") or ""),
            "date": str(fm["date"]) if fm.get("date") is not None else None,
            "updated": str(fm["updated"]) if fm.get("updated") is not None else None,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "version": self.version_of(data), "raw_content": raw, "frontmatter": fm,
        }

    def version(self, relative_path):
        try:
            data, _, _ = self.snapshot(self.path(relative_path), tolerate_encoding=True)
        except ContentError as error:
            if error.status == 404:
                return {"exists": False, "version": None}
            raise
        return {"exists": True, "version": self.version_of(data)}

    @staticmethod
    def directory_info(relative_path):
        name = relative_path.rsplit("/", 1)[-1]
        return {"relative_path": relative_path, "name": name, "label": strip_prefix(name),
                "section": relative_path.split("/")[0] if relative_path else ""}

    def list_content(self):
        visited = {self.content_root}

        def walk(directory, relative):
            directories, documents = [], []
            child_count, has_introduction = 0, False
            for entry in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), sort_key(p.name))):
                if entry.name.startswith((".", "_")) or entry.is_symlink():
                    continue
                rel = f"{relative}/{entry.name}" if relative else entry.name
                if entry.is_dir():
                    if RESOURCE_DIRECTORY.match(entry.name):
                        continue
                    try:
                        resolved = entry.resolve()
                        resolved.relative_to(self.content_root)
                    except (OSError, ValueError, RuntimeError):
                        continue
                    # Python 3.10 无 is_junction；解析路径即可排除 junction 和祖先回环。
                    if resolved != entry.absolute() or resolved in visited:
                        continue
                    visited.add(resolved)
                    nested_dirs, nested_docs, nested_count, introduction = walk(entry, rel)
                    empty_category = rel.startswith(("knowledge/", "blog/", "projects/")) and all(
                        item.name.startswith((".", "_")) for item in entry.iterdir())
                    if relative and not nested_count and not introduction and not empty_category:
                        continue
                    directories.append(self.directory_info(rel))
                    directories.extend(nested_dirs)
                    documents.extend(nested_docs)
                    child_count += 1
                elif entry.is_file() and entry.suffix.lower() in MD_EXTENSIONS:
                    try:
                        detail = self.detail(rel, summary=True)
                    except ContentError as error:
                        if error.status == 404:
                            continue
                        raise
                    documents.append({key: value for key, value in detail.items() if key not in {"raw_content", "frontmatter"}})
                    if detail["kind"] == "introduction":
                        has_introduction = True
                    else:
                        child_count += 1
            return directories, documents, child_count, has_introduction

        directories, documents, _, _ = walk(self.content_root, "")
        return {"directories": [self.directory_info("")] + directories, "documents": documents}

    def create(self, relative_path, raw_content, article=True):
        target = self.path(relative_path)
        if target.suffix.lower() != ".md":
            raise ContentError(400, "invalid_path", "新文档仅支持 .md")
        raw_content = raw_content.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        metadata, body = parse_markdown(raw_content)
        if article and not exempt(target.name):
            try:
                validate(raw_content, metadata, first_heading(body), creating=True)
            except ArticleError as error:
                raise ContentError(400, "invalid_article", str(error)) from error
        with self.lock:
            try:
                # O_EXCL 同时约束其他进程的同名新建，不会覆盖已有文件。
                with target.open("xb") as output:
                    try:
                        output.write(raw_content.encode("utf-8"))
                        output.flush()
                        os.fsync(output.fileno())
                    except BaseException:
                        output.close()
                        target.unlink(missing_ok=True)
                        raise
            except FileExistsError as error:
                raise ContentError(409, "already_exists", "目标已存在") from error
            except FileNotFoundError as error:
                raise ContentError(404, "not_found", "父目录不存在，请先显式创建目录") from error
            except OSError as error:
                raise ContentError(500, "write_failed", "创建文档失败") from error
            return self.detail(relative_path)

    def checked_snapshot(self, target, expected_version):
        if not expected_version:
            raise ContentError(428, "version_required", "必须提供读取时的 expected_version")
        data, _, _ = self.snapshot(target)
        if self.version_of(data) != expected_version:
            raise ContentError(409, "version_conflict", "文档已被外部修改，请读取最新内容")
        return data

    def save(self, relative_path, raw_content, expected_version, article=None):
        target = self.path(relative_path)
        with self.lock:
            previous = self.checked_snapshot(target, expected_version)
            metadata, body = parse_markdown(raw_content)
            old_raw = previous.decode("utf-8")
            old_metadata, _ = parse_markdown(old_raw)
            is_article = article is True or (article is None and all(field in old_metadata for field in FIELDS))
            if not exempt(target.name) and is_article:
                try:
                    raw_content = maintain_updated(old_raw, raw_content, old_metadata, metadata, first_heading(body))
                except ArticleError as error:
                    raise ContentError(400, "invalid_article", str(error)) from error
            new_data = raw_content.encode("utf-8")
            if previous != new_data:
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".desktop-", delete=False) as output:
                        temporary = Path(output.name)
                        output.write(new_data)
                        output.flush()
                        os.fsync(output.fileno())
                    os.replace(temporary, target)
                except OSError as error:
                    raise ContentError(500, "write_failed", "保存失败，原文档未被替换") from error
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
            return self.detail(relative_path)

    def delete(self, relative_path, expected_version, confirm):
        target = self.path(relative_path)
        if confirm is not True:
            raise ContentError(400, "confirmation_required", "删除必须明确确认目标文档")
        with self.lock:
            self.checked_snapshot(target, expected_version)
            try:
                target.unlink()
            except FileNotFoundError as error:
                raise ContentError(404, "not_found", "文档已不存在") from error
            except OSError as error:
                raise ContentError(500, "delete_failed", "删除失败") from error
        return {"deleted": relative_path}

    def create_directory(self, relative_path):
        target = self.path(relative_path, directory=True)
        with self.lock:
            try:
                target.mkdir(parents=True, exist_ok=False)
            except FileExistsError as error:
                raise ContentError(409, "already_exists", "目标已存在") from error
            except OSError as error:
                raise ContentError(500, "write_failed", "无法创建目录") from error
        return self.directory_info(relative_path)
