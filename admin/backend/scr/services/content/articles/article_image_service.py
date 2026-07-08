"""Article image file rules."""

from __future__ import annotations

from pathlib import Path
import re

from scr.core.exceptions import BadRequestError


class ArticleImageService:
    """Validate and name article image files."""

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
    allowed_mime_types = {
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
        ".gif": {"image/gif"},
        ".svg": {"image/svg+xml", "text/xml", "application/xml"},
    }
    max_size_bytes = 10 * 1024 * 1024
    image_name_pattern = re.compile(r"^[^\s.][^<>:\"\\|?*\x00-\x1f/\\]*$")
    unsafe_path_segment_pattern = re.compile(r'[<>:"\\|?*\x00-\x1f/]')

    def scan_files(self, image_dir: Path) -> list[Path]:
        files = [
            path
            for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in self.allowed_extensions
        ]
        return sorted(files, key=lambda item: item.name.lower())

    def validate_content(self, extension: str, content_type: str | None, content: bytes) -> None:
        normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
        allowed_types = self.allowed_mime_types.get(extension, set())
        if normalized_type and normalized_type not in allowed_types:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

        if extension == ".svg":
            self.validate_svg_content(content)
            return

        if not self.matches_image_magic(extension, content):
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

    @staticmethod
    def matches_image_magic(extension: str, content: bytes) -> bool:
        if extension == ".png":
            return content.startswith(b"\x89PNG\r\n\x1a\n")
        if extension in {".jpg", ".jpeg"}:
            return content.startswith(b"\xff\xd8\xff")
        if extension == ".gif":
            return content.startswith((b"GIF87a", b"GIF89a"))
        if extension == ".webp":
            return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
        return False

    @staticmethod
    def validate_svg_content(content: bytes) -> None:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type") from exc

        normalized = text.lower()
        if "<svg" not in normalized:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

        forbidden_patterns = ("<script", "javascript:", "onload=", "onclick=", "onerror=", "http://", "https://")
        if any(pattern in normalized for pattern in forbidden_patterns):
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

    def build_safe_stem(self, value: str) -> str:
        normalized = value.strip()
        normalized = re.sub(r"[\s_]+", "-", normalized)
        normalized = self.unsafe_path_segment_pattern.sub("-", normalized)
        normalized = re.sub(r"-+", "-", normalized).strip("-. ")
        if not normalized or normalized in {".", ".."} or ".." in normalized:
            raise BadRequestError("文件名无法生成安全路径片段。", code="invalid_file_name")
        return normalized

    def validate_name(self, image_name: str) -> None:
        if (
            not image_name
            or "/" in image_name
            or "\\" in image_name
            or image_name in {".", ".."}
            or ".." in image_name
            or image_name.rstrip(" .") != image_name
            or not self.image_name_pattern.fullmatch(image_name)
            or Path(image_name).suffix.lower() not in self.allowed_extensions
        ):
            raise BadRequestError(
                "图片名包含路径分隔符或非法字符。",
                code="invalid_image_name",
                details={"image_name": image_name},
            )

    @staticmethod
    def next_available_path(image_dir: Path, stem: str, extension: str) -> Path:
        target = image_dir / f"{stem}{extension}"
        if not target.exists():
            return target

        index = 1
        while True:
            candidate = image_dir / f"{stem}-{index}{extension}"
            if not candidate.exists():
                return candidate
            index += 1
