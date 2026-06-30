"""文件系统服务。

封装对 docs / blog 内容目录的扫描与路径解析，所有对外路径操作均经
ensure_child_path 校验，防止越界访问。
"""

from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.models.article import ArticleType


class FileSystemService:
    """提供文章相关的文件系统读取能力。"""

    content_extensions = {".md", ".mdx"}  # 视为有效文章的扩展名集合

    def content_root(self, article_type: ArticleType) -> Path:
        """返回指定类型对应的内容根目录；未知类型直接抛 ValueError。"""
        if article_type == ArticleType.docs:
            return settings.docs_dir
        if article_type == ArticleType.blog:
            return settings.blog_dir
        raise ValueError(f"Unsupported article type: {article_type}")

    def scan_article_files(self, article_type: ArticleType) -> list[Path]:
        """递归扫描某类型下全部文章文件，按相对路径排序返回。"""
        root = self.content_root(article_type)
        if not root.exists():
            return []

        files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in self.content_extensions
        ]
        # 按相对根目录的 posix 路径排序，保证列表稳定可预期
        return sorted(files, key=lambda item: item.relative_to(root).as_posix())

    def resolve_article_path(self, article_type: ArticleType, relative_path: str) -> Path:
        """将相对路径拼接到内容根并做越界校验，非法路径抛 BadRequestError。"""
        root = self.content_root(article_type)
        target = root / relative_path

        try:
            return ensure_child_path(root, target)
        except PathSecurityError as exc:
            raise BadRequestError("文章路径越界，已拒绝访问。", code="path_out_of_scope") from exc

    def relative_posix_path(self, article_type: ArticleType, path: Path) -> str:
        """计算文件相对于内容根的 posix 路径，用于对外展示与 ID 编码。"""
        root = self.content_root(article_type)
        return path.resolve().relative_to(root.resolve()).as_posix()
