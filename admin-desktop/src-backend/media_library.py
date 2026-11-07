"""Article-owned media and deletion previews."""

import base64
import binascii
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from xml.etree import ElementTree

from content_mutations import document_snapshots, mutable_path, plan_digest
from content_store import ContentError, IMAGE_TYPES, MD_EXTENSIONS
from markdown_links import destinations, relative_reference, resolve_reference

MAX_IMAGE_SIZE = 12 * 1024 * 1024
SVG_NS = "{http://www.w3.org/2000/svg}"
SVG_ELEMENTS = frozenset(
    "svg g defs symbol use title desc path rect circle ellipse line polyline polygon text tspan "
    "linearGradient radialGradient stop clipPath mask pattern marker".split()
)


def image_directory(document):
    path = PurePosixPath(document)
    return str(path.with_name(path.stem + "-images"))


def image_owner(directory):
    stem = directory.name.removesuffix("-images").casefold()
    owners = [
        path for path in directory.parent.iterdir()
        if path.stem.casefold() == stem and path.suffix.lower() in MD_EXTENSIONS
        and path.is_file() and not path.is_symlink() and path.resolve() == path
    ]
    if not owners:
        raise ContentError(404, "not_found", "配图目录没有对应的 Markdown 文档")
    if len(owners) != 1:
        raise ContentError(409, "ambiguous_media_owner", "同名 Markdown 文档共享配图目录，请先处理同名文档")
    return owners[0]


def safe_svg(data):
    try:
        text = data.decode("utf-8-sig")
        # Reject entity expansion and processing instructions, including external stylesheets.
        text = re.sub(r"^\s*<\?xml\s[^?]*\?>", "", text, count=1)
        if "<!" in text.replace("<!--", "") or "<?" in text:
            return False
        root = ElementTree.fromstring(text)
    except (UnicodeError, ElementTree.ParseError):
        return False
    if root.tag not in {"svg", SVG_NS + "svg"}:
        return False
    for element in root.iter():
        if element.tag.removeprefix(SVG_NS) not in SVG_ELEMENTS:
            return False
        for name, value in element.attrib.items():
            local = name.rsplit("}", 1)[-1].lower()
            if local.startswith("on") or local in {"style", "base"} or "\\" in value:
                return False
            if local == "href" and not value.startswith("#"):
                return False
            if re.search(r"url\s*\(", value, re.IGNORECASE) and not re.fullmatch(r"url\(\s*#[\w.-]+\s*\)", value):
                return False
    return True


def valid_image(data, suffix):
    if suffix == ".svg":
        return safe_svg(data)
    if suffix in {".jpg", ".jpeg"}:
        return data.startswith(b"\xff\xd8\xff")
    if suffix == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix == ".gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if suffix == ".webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if suffix == ".avif":
        return data[4:8] == b"ftyp" and any(brand in data[8:32] for brand in (b"avif", b"avis"))
    if suffix == ".bmp":
        return data.startswith(b"BM")
    return suffix == ".ico" and data.startswith(b"\x00\x00\x01\x00")


def entry(document, relative_path, size, *, alt=None):
    target = PurePosixPath(relative_path)
    if alt is None:
        alt = target.stem
    label = re.sub(r"([\\\[\]])", r"\\\1", alt)
    return {
        "relative_path": relative_path,
        "name": target.name,
        "mime_type": IMAGE_TYPES[target.suffix.lower()],
        "size": size,
        "markdown": f"![{label}]({relative_reference(document, relative_path)})",
    }


class MediaLibrary:
    def __init__(self, store):
        self.store = store

    def article_directory(self, document):
        article = mutable_path(self.store, document)
        if not article.is_file():
            raise ContentError(404, "not_found", "请先保存文档再管理配图")
        relative = image_directory(document)
        directory = mutable_path(self.store, relative, directory=True)
        image_owner(directory)
        return relative, directory

    def list_images(self, document):
        with self.store.lock:
            relative, directory = self.article_directory(document)
            if not directory.exists():
                return []
            if not directory.is_dir():
                raise ContentError(409, "already_exists", "同名文件占用了配图目录")
            return [
                entry(document, f"{relative}/{image.name}", image.stat().st_size)
                for image in sorted(directory.iterdir(), key=lambda path: path.name.casefold())
                if image.suffix.lower() in IMAGE_TYPES and not image.name.startswith((".", "_"))
                and not image.is_symlink() and image.resolve() == image and image.is_file()
            ]

    def import_image(self, document, filename, encoded):
        if "/" in filename or "\\" in filename:
            raise ContentError(400, "invalid_path", "图片名称不能包含目录分隔符")
        if len(encoded) > ((MAX_IMAGE_SIZE + 2) // 3) * 4:
            raise ContentError(413, "image_too_large", "单张图片不能超过 12 MiB")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ContentError(400, "invalid_image", "图片数据不是有效的 Base64") from error
        if len(data) > MAX_IMAGE_SIZE:
            raise ContentError(413, "image_too_large", "单张图片不能超过 12 MiB")
        original = PurePosixPath(filename)
        if not valid_image(data, original.suffix.lower()):
            raise ContentError(400, "invalid_image", "不支持该图片格式或图片内容与扩展名不符")
        with self.store.lock:
            relative, directory = self.article_directory(document)
            mutable_path(self.store, f"{relative}/{filename}", directory=True)
            created = False
            temporary = None
            published = False
            try:
                if not directory.exists():
                    directory.mkdir()
                    created = True
                if not directory.is_dir():
                    raise ContentError(409, "already_exists", "同名文件占用了配图目录")
                with tempfile.NamedTemporaryFile(dir=directory, prefix=".desktop-", delete=False) as output:
                    temporary = Path(output.name)
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                taken = {path.name.casefold() for path in directory.iterdir()}
                for number in range(1, 10_000):
                    name = filename if number == 1 else f"{original.stem}-{number}{original.suffix}"
                    if name.casefold() in taken:
                        continue
                    try:
                        if os.name == "nt":
                            os.rename(temporary, directory / name)
                        else:
                            os.link(temporary, directory / name)
                    except FileExistsError:
                        continue
                    published = True
                    return entry(document, f"{relative}/{name}", len(data), alt=original.stem)
                raise ContentError(409, "already_exists", "同名图片过多，请更换名称")
            except OSError as error:
                raise ContentError(500, "write_failed", "无法写入配图") from error
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
                if created and not published:
                    try:
                        directory.rmdir()
                    except OSError:
                        pass

    def delete_plan(self, relative_path):
        with self.store.lock:
            target = mutable_path(self.store, relative_path, directory=True)
            if not target.parent.name.endswith("-images"):
                raise ContentError(400, "invalid_path", "只可从文档配图目录删除图片")
            self.store.image(relative_path)
            image_owner(target.parent)
            references = []
            versions = []
            for document, data in document_snapshots(self.store):
                count = sum(
                    bool(reference and reference[0] == relative_path)
                    for reference in (resolve_reference(document, span.value) for span in destinations(data))
                )
                if count:
                    references.append({"relative_path": document, "count": count})
                    versions.append((document, self.store.version_of(data)))
            with target.open("rb") as image:
                version = hashlib.sha256()
                for chunk in iter(lambda: image.read(1024 * 1024), b""):
                    version.update(chunk)
            return {"relative_path": relative_path, "references": references,
                    "plan_id": plan_digest([relative_path, version.hexdigest(), sorted(versions)])}

    def delete(self, relative_path, plan_id, confirm):
        if confirm is not True:
            raise ContentError(400, "confirmation_required", "删除图片前须确认引用范围")
        with self.store.lock:
            if self.delete_plan(relative_path)["plan_id"] != plan_id:
                raise ContentError(409, "stale_plan", "图片或引用已改变，请重新查看删除影响")
            try:
                mutable_path(self.store, relative_path, directory=True).unlink()
            except OSError as error:
                raise ContentError(500, "delete_failed", "无法删除配图") from error
            return {"deleted": relative_path}
