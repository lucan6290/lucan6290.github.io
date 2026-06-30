"""文章业务服务层（content 子包）。

协调 FileSystemService、MarkdownService 与 SidebarService，提供文章的
列表查询、详情读取、创建写入，以及 Front Matter 校验与文章 ID 编解码。
docs 与 blog 两种类型在路径约定、frontmatter 字段与侧边栏登记上存在差异，
由各自的私有方法分别处理。
"""

import base64
from datetime import datetime
import re
import shutil
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError, PreconditionRequiredError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.models.article import ArticleType
from scr.schemas.article import (
    ArticleCreateDTO,
    ArticleDetailDTO,
    ArticleImageCheckDTO,
    ArticleImageListDTO,
    ArticleListResponseDTO,
    ArticleMoveDTO,
    ArticleSummaryDTO,
    ArticleUpdateDTO,
    ArticleValidationResultDTO,
    ImageDTO,
    ValidationIssueDTO,
)
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.category_service import CategoryService
from scr.services.content.filesystem_service import FileSystemService
from scr.services.content.markdown_service import MarkdownService, ParsedMarkdown
from scr.services.content.sidebar_service import SidebarService
from scr.services.content.tag_service import TagService


class ArticleService:
    """文章核心业务服务，供 API 端点直接调用。"""

    # 匹配 blog 文件名形如 2024-01-01-my-post 的日期前缀，用于在缺省 slug 时回退提取
    date_slug_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")
    date_prefix_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")  # 仅匹配日期前缀，用于校验/截取 blog date
    slug_segment_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*$")  # 合法 slug 段规则：小写字母/数字/连字符
    unsafe_path_segment_pattern = re.compile(r'[<>:"\\|?*\x00-\x1f/]')  # Windows 与 POSIX 路径片段危险字符
    markdown_image_pattern = re.compile(r"!\[[^\]]*\]\((?P<src>[^)]+)\)")
    html_image_pattern = re.compile(r"<img\b[^>]*\bsrc=[\"'](?P<src>[^\"']+)[\"']", re.IGNORECASE)
    image_name_pattern = re.compile(r"^[^\s.][^<>:\"\\|?*\x00-\x1f/\\]*$")
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
    image_mime_types = {
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
        ".gif": {"image/gif"},
        ".svg": {"image/svg+xml", "text/xml", "application/xml"},
    }
    max_image_size_bytes = 10 * 1024 * 1024
    sortable_fields = {"title", "date", "updated_at", "relative_path", "type"}

    def __init__(self) -> None:
        # 聚合三个底层服务，按职责分工协作
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.sidebar = SidebarService()
        self.category = CategoryService()
        self.tags = TagService()

    def list_articles(
        self,
        article_type: ArticleType | None = None,
        keyword: str | None = None,
        tag: str | None = None,
        author: str | None = None,
        category: str | None = None,
        has_issues: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str | None = None,
    ) -> ArticleListResponseDTO:
        """列出文章摘要，支持过滤、排序与分页。

        article_type 为 None 时同时扫描 docs 与 blog；keyword 命中标题/描述/路径/标签等任一字段即保留。
        """
        requested_types = [article_type] if article_type else [ArticleType.docs, ArticleType.blog]
        registered_doc_ids = self.sidebar.list_registered_doc_ids()
        blog_authors = self._load_blog_authors()

        articles: list[ArticleSummaryDTO] = []
        for current_type in requested_types:
            for path in self.filesystem.scan_article_files(current_type):
                summary = self._build_summary(path, current_type, registered_doc_ids, blog_authors)
                if self._matches_filters(
                    summary,
                    keyword=keyword,
                    tag=tag,
                    author=author,
                    category=category,
                    has_issues=has_issues,
                ):
                    articles.append(summary)

        articles = self._sort_articles(articles, sort)
        total = len(articles)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        return ArticleListResponseDTO(
            items=articles[start_index:end_index],
            page=page,
            page_size=page_size,
            total=total,
            has_next=end_index < total,
        )

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """创建文章入口：按类型分发到 docs / blog 各自的创建流程。"""
        if payload.type == ArticleType.docs:
            return self._create_docs_article(payload)
        return self._create_blog_article(payload)

    def get_article(self, article_id: str) -> ArticleDetailDTO:
        """根据文章 ID 读取详情；文件不存在时抛 NotFoundError。"""
        article_type, relative_path = self._decode_article_id(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        summary = self._build_summary(
            path=path,
            article_type=article_type,
            registered_doc_ids=self.sidebar.list_registered_doc_ids(),
            blog_authors=self._load_blog_authors(),
            parsed=parsed,
        )

        # 约定图片目录与文章同名，后缀为 -imgs
        image_dir = path.with_name(f"{path.stem}-imgs")

        return ArticleDetailDTO(
            **summary.model_dump(),
            frontmatter=parsed.frontmatter,
            body=parsed.body,
            raw_content=parsed.raw_content,
            image_dir=image_dir.as_posix() if image_dir.exists() else None,
        )

    def save_article(self, article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
        """保存文章内容，不改变文章路径，并使用 expected_version 做乐观锁校验。"""
        if not payload.expected_version or not payload.expected_version.strip():
            raise PreconditionRequiredError("缺少 expected_version。", code="version_required")

        article_type, relative_path = self._decode_article_id(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        current_version = self._file_version(path)
        if payload.expected_version != current_version:
            raise ConflictError(
                "文件版本已变化，请重新读取后再保存。",
                code="version_conflict",
                details={
                    "expected_version": payload.expected_version,
                    "current_version": current_version,
                },
            )

        self._validate_update_frontmatter(article_type, payload.frontmatter)
        raw_content = self.markdown.compose(payload.frontmatter, payload.body)
        path.write_text(raw_content, encoding="utf-8")

        return self.get_article(article_id)

    def validate_article(self, article_id: str) -> ArticleValidationResultDTO:
        """校验单篇文章，返回 Front Matter、侧边栏与本地图片引用问题。"""
        article_type, relative_path = self._decode_article_id(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        summary = self._build_summary(
            path=path,
            article_type=article_type,
            registered_doc_ids=self.sidebar.list_registered_doc_ids(),
            blog_authors=self._load_blog_authors(),
            parsed=parsed,
        )

        issues = [*summary.issues, *self._validate_image_references(path, parsed.body)]
        return ArticleValidationResultDTO(article_id=article_id, issues=issues)

    def encode_article_id(self, article_type: ArticleType, relative_path: str) -> str:
        """将文章类型与相对路径编码为对外 article_id。"""
        return self._encode_article_id(article_type, relative_path)

    def list_article_images(self, article_id: str) -> ArticleImageListDTO:
        """列出文章同名图片目录中的图片资源。"""
        article_type, relative_path = self._decode_article_id(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        image_dir = path.with_name(f"{path.stem}-imgs")
        if not image_dir.exists() or not image_dir.is_dir():
            return ArticleImageListDTO(article_id=article_id, image_dir=None, images=[])

        referenced_sources = self._referenced_image_source_set(parsed.body)
        images: list[ImageDTO] = []
        for image_path in self._scan_image_files(image_dir):
            markdown_url = f"./{image_dir.name}/{image_path.name}"
            relative_project_path = self._project_relative_posix_path(image_path)
            images.append(
                ImageDTO(
                    name=image_path.name,
                    relative_path=relative_project_path,
                    markdown_url=markdown_url,
                    markdown=f"![{image_path.stem}]({markdown_url})",
                    size=image_path.stat().st_size,
                    referenced=self._is_image_referenced(image_dir.name, image_path.name, referenced_sources),
                    created_at=self._file_created_at(image_path),
                )
            )

        return ArticleImageListDTO(
            article_id=article_id,
            image_dir=self._project_relative_posix_path(image_dir),
            images=images,
        )

    def upload_article_image(
        self,
        article_id: str,
        *,
        original_filename: str,
        content_type: str | None,
        content: bytes,
        slug: str | None = None,
        alt: str | None = None,
    ) -> ImageDTO:
        """上传图片到文章同名图片目录，并返回可插入 Markdown 的图片信息。"""
        article_type, relative_path = self._decode_article_id(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        extension = Path(original_filename).suffix.lower()
        if extension not in self.image_extensions:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")
        if len(content) > self.max_image_size_bytes:
            raise BadRequestError(
                "文件超过大小限制。",
                code="file_too_large",
                details={"max_size": self.max_image_size_bytes, "actual_size": len(content)},
            )
        self._validate_image_content(extension, content_type, content)

        safe_stem = self._build_safe_image_stem(slug or Path(original_filename).stem)
        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        image_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._next_available_image_path(image_dir, safe_stem, extension)
        target_path.write_bytes(content)

        markdown_url = f"./{image_dir.name}/{target_path.name}"
        alt_text = alt.strip() if alt and alt.strip() else target_path.stem
        return ImageDTO(
            name=target_path.name,
            relative_path=self._project_relative_posix_path(target_path),
            markdown_url=markdown_url,
            markdown=f"![{alt_text}]({markdown_url})",
            size=target_path.stat().st_size,
            referenced=False,
            created_at=self._file_created_at(target_path),
        )

    def check_article_images(self, article_id: str) -> ArticleImageCheckDTO:
        """检查文章图片目录与正文图片引用之间的差异。"""
        article_type, relative_path = self._decode_article_id(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = article_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        image_files = self._scan_image_files(image_dir) if image_dir.exists() and image_dir.is_dir() else []
        referenced_sources = self._referenced_image_source_set(parsed.body)
        referenced_images: list[str] = []
        unused_images: list[str] = []

        for image_path in image_files:
            if self._is_image_referenced(image_dir.name, image_path.name, referenced_sources):
                referenced_images.append(image_path.name)
            else:
                unused_images.append(image_path.name)

        missing_references, out_of_scope_references = self._missing_image_references(article_path, parsed.body)

        return ArticleImageCheckDTO(
            article_id=article_id,
            image_dir=self._project_relative_posix_path(image_dir) if image_dir.exists() and image_dir.is_dir() else None,
            referenced_images=referenced_images,
            unused_images=unused_images,
            missing_references=missing_references,
            out_of_scope_references=out_of_scope_references,
        )

    def get_article_image_path(self, article_id: str, image_name: str) -> Path:
        """返回文章同名图片目录中的安全图片路径。"""
        self._validate_image_name(image_name)

        article_type, relative_path = self._decode_article_id(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        try:
            image_path = ensure_child_path(image_dir, image_dir / image_name)
        except PathSecurityError as exc:
            raise BadRequestError("图片路径越界，已拒绝访问。", code="path_out_of_scope") from exc

        if not image_path.exists() or not image_path.is_file():
            raise NotFoundError("图片不存在。", code="image_not_found")

        return image_path

    def delete_article_image(
        self,
        article_id: str,
        image_name: str,
        *,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除文章同名图片目录中的单个图片，默认只返回影响分析。"""
        self._validate_image_name(image_name)

        article_type, relative_path = self._decode_article_id(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        try:
            image_path = ensure_child_path(image_dir, image_dir / image_name)
        except PathSecurityError as exc:
            raise BadRequestError("图片路径越界，已拒绝访问。", code="path_out_of_scope") from exc

        if not image_path.exists() or not image_path.is_file():
            raise NotFoundError("图片不存在。", code="image_not_found")

        raw_content = article_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        referenced_sources = self._referenced_image_source_set(parsed.body)
        is_referenced = self._is_image_referenced(image_dir.name, image_name, referenced_sources)
        warnings = [f"图片 {image_name} 仍被正文引用，删除后文章会出现缺失图片。"] if is_referenced else []

        if not dry_run and is_referenced and not confirm:
            raise ConflictError(
                "图片仍被正文引用，请确认后再删除。",
                code="image_still_referenced",
                details={"image_name": image_name},
            )
        if not dry_run and not confirm:
            raise BadRequestError("删除图片需要显式确认。", code="confirmation_required")

        target = self._project_relative_posix_path(image_path)
        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=[
                FileChangeDTO(
                    action="delete",
                    target=target,
                    description=(
                        f"删除文章图片 {image_name}"
                        if dry_run
                        else f"已删除文章图片 {image_name}"
                    ),
                )
            ],
            warnings=warnings,
        )

        if dry_run:
            return plan

        image_path.unlink()
        return plan

    def delete_article(
        self,
        article_id: str,
        *,
        with_images: bool = False,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除文章文件；docs 文章会同步移除 sidebars.ts 中的 doc_id。"""
        article_type, relative_path = self._decode_article_id(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        raw_content = article_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        has_image_dir = image_dir.exists() and image_dir.is_dir()
        doc_id = self.sidebar.doc_id_from_relative_path(relative_path) if article_type == ArticleType.docs else None
        sidebar_registered = doc_id in self.sidebar.list_registered_doc_ids() if doc_id else False
        references = self._find_article_references(article_type, relative_path, parsed)

        if not dry_run and references and not confirm:
            raise ConflictError(
                "文章仍被站内内容引用，请确认后再删除。",
                code="article_has_references",
                details={"references": references},
            )
        if not dry_run and not confirm:
            raise BadRequestError("删除文章需要显式确认。", code="confirmation_required")

        changes = [
            FileChangeDTO(
                action="delete",
                target=self._project_relative_posix_path(article_path),
                description="删除文章文件" if dry_run else "已删除文章文件",
            )
        ]

        if doc_id and sidebar_registered:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self._project_relative_posix_path(settings.sidebars_path),
                    description=(
                        f"移除 docs 文章 ID {doc_id}"
                        if dry_run
                        else f"已移除 docs 文章 ID {doc_id}"
                    ),
                )
            )

        warnings: list[str] = []
        if has_image_dir and with_images:
            changes.append(
                FileChangeDTO(
                    action="delete",
                    target=self._project_relative_posix_path(image_dir),
                    description="删除文章图片目录" if dry_run else "已删除文章图片目录",
                )
            )
        elif has_image_dir:
            warnings.append("文章图片目录存在，默认不会删除，除非 with_images=true。")

        if references:
            warnings.append("文章仍被站内内容引用，删除前请确认引用影响。")

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=warnings,
        )

        if dry_run:
            return plan

        if doc_id and sidebar_registered:
            self.sidebar.remove_doc_id(doc_id)
        if has_image_dir and with_images:
            safe_image_dir = ensure_child_path(article_path.parent, image_dir)
            shutil.rmtree(safe_image_dir)
        article_path.unlink()
        return plan

    def move_article(self, article_id: str, payload: ArticleMoveDTO) -> MutationPlanDTO:
        """移动或重命名文章；默认只返回影响分析。"""
        article_type, relative_path = self._decode_article_id(article_id)
        if payload.target_type != article_type:
            raise BadRequestError(
                "当前仅支持在同一内容类型内移动或重命名文章。",
                code="invalid_target_type",
                details={"source_type": article_type.value, "target_type": payload.target_type.value},
            )

        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        self._validate_path_segment(payload.target_slug, field_name="target_slug")
        raw_content = article_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw_content)
        target_relative_path, new_frontmatter = self._build_move_target(article_type, relative_path, payload, parsed)
        target_path = self.filesystem.resolve_article_path(payload.target_type, target_relative_path)
        if target_path.exists():
            raise ConflictError("目标文章已存在。", code="target_article_exists")

        image_dir = article_path.with_name(f"{article_path.stem}-imgs")
        target_image_dir = target_path.with_name(f"{target_path.stem}-imgs")
        has_image_dir = image_dir.exists() and image_dir.is_dir()
        updated_body = (
            self._replace_moved_article_image_dir_refs(parsed.body, image_dir.name, target_image_dir.name)
            if has_image_dir
            else parsed.body
        )
        if has_image_dir and target_image_dir.exists():
            raise ConflictError(
                "目标文章图片目录已存在。",
                code="target_article_exists",
                details={"target": self._project_relative_posix_path(target_image_dir)},
            )

        old_doc_id = self.sidebar.doc_id_from_relative_path(relative_path) if article_type == ArticleType.docs else None
        new_doc_id = (
            self.sidebar.doc_id_from_relative_path(target_relative_path)
            if payload.target_type == ArticleType.docs
            else None
        )
        if old_doc_id and not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")
        sidebar_registered = old_doc_id in self.sidebar.list_registered_doc_ids() if old_doc_id else False
        link_replacements = self._planned_article_link_replacements(
            article_type,
            relative_path,
            target_relative_path,
            parsed.frontmatter,
            new_frontmatter,
        )
        link_changes = self._find_link_replacement_targets(article_path, link_replacements) if payload.replace_links else []

        if not payload.dry_run and not payload.confirm:
            raise BadRequestError("移动文章需要显式确认。", code="confirmation_required")

        warnings: list[str] = []
        if not payload.replace_links and self._find_link_replacement_targets(article_path, link_replacements):
            warnings.append("站内旧链接不会自动替换，除非 replace_links=true。")
        if old_doc_id and not sidebar_registered:
            warnings.append("原 docs 文章 ID 未登记在 sidebars.ts，移动时不会产生侧边栏替换。")

        changes = [
            FileChangeDTO(
                action="move",
                target=self._project_relative_posix_path(target_path),
                from_=self._project_relative_posix_path(article_path),
                to=self._project_relative_posix_path(target_path),
                description="移动文章文件" if payload.dry_run else "已移动文章文件",
            )
        ]

        if has_image_dir:
            changes.append(
                FileChangeDTO(
                    action="move",
                    target=self._project_relative_posix_path(target_image_dir),
                    from_=self._project_relative_posix_path(image_dir),
                    to=self._project_relative_posix_path(target_image_dir),
                    description="移动文章图片目录" if payload.dry_run else "已移动文章图片目录",
                )
            )

        if updated_body != parsed.body:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self._project_relative_posix_path(target_path),
                    description="更新文章内图片目录引用" if payload.dry_run else "已更新文章内图片目录引用",
                )
            )

        if old_doc_id and new_doc_id and sidebar_registered and old_doc_id != new_doc_id:
            changes.append(
                FileChangeDTO(
                    action="replace",
                    target=self._project_relative_posix_path(settings.sidebars_path),
                    from_=old_doc_id,
                    to=new_doc_id,
                    description="替换 docs 文章 ID" if payload.dry_run else "已替换 docs 文章 ID",
                )
            )

        for path in link_changes:
            changes.append(
                FileChangeDTO(
                    action="replace",
                    target=self._project_relative_posix_path(path),
                    description="替换站内旧链接" if payload.dry_run else "已替换站内旧链接",
                )
            )

        plan = MutationPlanDTO(
            dry_run=payload.dry_run,
            requires_confirmation=payload.dry_run,
            changes=changes,
            warnings=warnings,
        )

        if payload.dry_run:
            return plan

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if article_type == ArticleType.blog or updated_body != parsed.body:
            article_path.write_text(self.markdown.compose(new_frontmatter, updated_body), encoding="utf-8")

        if old_doc_id and new_doc_id and sidebar_registered and old_doc_id != new_doc_id:
            self.sidebar.replace_doc_id(old_doc_id, new_doc_id)

        if payload.replace_links:
            self._replace_article_links(article_path, link_replacements)

        article_path.replace(target_path)
        if has_image_dir:
            shutil.move(str(image_dir), str(target_image_dir))

        return plan

    def _create_docs_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """创建 docs 文章：校验 slug 与分类段 → 组装路径与 frontmatter → 写文件并登记侧边栏。

        写文件或登记侧边栏失败时回滚已写入的文章文件，并恢复注册表快照，
        避免产生孤立文章与残留分类条目。
        """
        self._validate_path_segment(payload.slug, field_name="slug")
        for segment in payload.category_path:
            self._validate_path_segment(segment, field_name="category_path")

        # 相对路径 = 分类目录 / slug.md
        relative_path = "/".join([*payload.category_path, f"{payload.slug}.md"])
        path = self.filesystem.resolve_article_path(ArticleType.docs, relative_path)
        if path.exists():
            raise ConflictError("docs 文章已存在。", code="article_already_exists")

        # 登记分类前先快照注册表，便于后续写入失败时整体回滚
        registry_snapshot = self.category.snapshot_registry()
        category_labels = self.category.ensure_category_path(ArticleType.docs, payload.category_path)

        frontmatter: dict[str, Any] = {"title": payload.title}
        if payload.description:
            frontmatter["description"] = payload.description
        if payload.sidebar_position is not None:
            frontmatter["sidebar_position"] = payload.sidebar_position

        raw_content = self.markdown.compose(frontmatter, payload.body)
        doc_id = self.sidebar.doc_id_from_relative_path(relative_path)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(raw_content, encoding="utf-8")
            self.sidebar.ensure_doc_id(doc_id, payload.category_path, category_labels)  # 同步登记到 sidebars.ts
        except Exception:
            # 回滚：删除已写入的文章文件并恢复注册表快照，保证不残留半成品
            if path.exists():
                path.unlink()
            self.category.restore_registry(registry_snapshot)
            raise

        return self.get_article(self._encode_article_id(ArticleType.docs, relative_path))

    def _create_blog_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """创建 blog 文章：校验 slug 与作者 → 以日期前缀命名 → 组装 frontmatter 并写文件。"""
        self._validate_path_segment(payload.slug, field_name="slug")
        self._validate_blog_authors(payload.authors)
        self.tags.ensure_tags(payload.tags)

        # date 缺省时取当前上海时区时间；文件名统一带 YYYY-MM-DD- 前缀
        date_value = payload.date or self._now_shanghai_iso()
        date_prefix = self._date_prefix(date_value)
        relative_path = f"{date_prefix}-{payload.slug}.md"
        path = self.filesystem.resolve_article_path(ArticleType.blog, relative_path)
        if path.exists():
            raise ConflictError("blog 文章已存在。", code="article_already_exists")

        frontmatter: dict[str, Any] = {
            "slug": payload.slug,
            "title": payload.title,
            # 单作者写为标量，多作者保留列表，贴合 Docusaurus 约定
            "authors": payload.authors[0] if len(payload.authors) == 1 else payload.authors,
            "tags": payload.tags,
        }
        if payload.description:
            frontmatter["description"] = payload.description
        frontmatter["date"] = date_value

        raw_content = self.markdown.compose(frontmatter, payload.body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw_content, encoding="utf-8")

        return self.get_article(self._encode_article_id(ArticleType.blog, relative_path))

    def _build_summary(
        self,
        path: Path,
        article_type: ArticleType,
        registered_doc_ids: set[str],
        blog_authors: set[str],
        parsed: ParsedMarkdown | None = None,
    ) -> ArticleSummaryDTO:
        """由文件路径与解析结果组装文章摘要，并附加类型相关的校验问题。"""
        raw_content = path.read_text(encoding="utf-8")
        parsed = parsed or self.markdown.parse(raw_content)
        relative_path = self.filesystem.relative_posix_path(article_type, path)
        frontmatter = parsed.frontmatter

        slug = self._resolve_slug(article_type, relative_path, frontmatter)
        issues = [*parsed.issues]
        sidebar_registered: bool | None = None

        if article_type == ArticleType.docs:
            # docs 类型：slug 取 doc_id，并校验是否登记到 sidebars.ts
            doc_id = self.sidebar.doc_id_from_relative_path(relative_path)
            slug = doc_id
            sidebar_registered = doc_id in registered_doc_ids
            issues.extend(self._validate_docs(frontmatter, sidebar_registered))
        else:
            # blog 类型：仅做 frontmatter 校验，无侧边栏登记概念
            issues.extend(self._validate_blog(frontmatter, blog_authors))

        tags = self._list_value(frontmatter.get("tags"))
        category_path, category_label = self.category.resolve_article_category(
            article_type,
            self._category_path(article_type, relative_path, frontmatter),
            self._category_candidates(frontmatter),
        )

        return ArticleSummaryDTO(
            id=self._encode_article_id(article_type, relative_path),
            type=article_type,
            type_label=self.category.type_label(article_type),
            title=self._string_value(frontmatter.get("title")),
            description=self._string_value(frontmatter.get("description")),
            relative_path=relative_path,
            route=self._build_route(article_type, slug),
            slug=slug,
            tags=tags,
            authors=self._list_value(frontmatter.get("authors")),
            category_path=category_path,
            category_label=category_label,
            sidebar_registered=sidebar_registered,
            version=self._file_version(path),
            updated_at=self._file_updated_at(path),
            issues=issues,
        )

    def _validate_update_frontmatter(self, article_type: ArticleType, frontmatter: dict[str, Any]) -> None:
        """保存文章前校验 Front Matter 是否满足当前内容类型的硬约束。"""
        issues: list[ValidationIssueDTO]
        if article_type == ArticleType.docs:
            issues = self._validate_docs(frontmatter, sidebar_registered=True)
            blocking_issues = [
                issue
                for issue in issues
                if issue.severity == "error" and issue.code != "docs_sidebar_missing"
            ]
        else:
            issues = self._validate_blog(frontmatter, self._load_blog_authors())
            blocking_issues = [issue for issue in issues if issue.severity == "error"]

            slug = self._string_value(frontmatter.get("slug"))
            if slug:
                try:
                    self._validate_slug_segment(slug, field_name="slug")
                except BadRequestError as exc:
                    raise BadRequestError(
                        "Front Matter 不符合内容类型规则。",
                        code="frontmatter_invalid",
                        details={"issues": [{"code": exc.code, "message": exc.message}]},
                    ) from exc

            date_value = self._string_value(frontmatter.get("date"))
            if date_value:
                try:
                    self._date_prefix(date_value)
                except BadRequestError as exc:
                    raise BadRequestError(
                        "Front Matter 不符合内容类型规则。",
                        code="frontmatter_invalid",
                        details={"issues": [{"code": exc.code, "message": exc.message}]},
                    ) from exc

        if blocking_issues:
            raise BadRequestError(
                "Front Matter 不符合内容类型规则。",
                code="frontmatter_invalid",
                details={"issues": [issue.model_dump() for issue in blocking_issues]},
            )

    def _validate_docs(self, frontmatter: dict[str, Any], sidebar_registered: bool) -> list[ValidationIssueDTO]:
        """校验 docs 文章：title 必填、description 建议、必须登记到 sidebars.ts。"""
        issues: list[ValidationIssueDTO] = []

        if not frontmatter.get("title"):
            issues.append(
                ValidationIssueDTO(
                    code="docs_title_missing",
                    message="docs 文章缺少 title。",
                    severity="error",
                )
            )
        if not frontmatter.get("description"):
            issues.append(
                ValidationIssueDTO(
                    code="docs_description_missing",
                    message="docs 文章建议填写 description。",
                )
            )
        if not sidebar_registered:
            issues.append(
                ValidationIssueDTO(
                    code="docs_sidebar_missing",
                    message="docs 文章尚未登记到 site/sidebars.ts。",
                    severity="error",
                )
            )

        return issues

    def _validate_blog(self, frontmatter: dict[str, Any], known_authors: set[str]) -> list[ValidationIssueDTO]:
        """校验 blog 文章：title/slug/authors/tags 必填，description/date 建议，作者必须存在于 authors.yml。

        注意：此处为"软"校验，问题计入 issues 返回；创建时的"硬"拦截见 _validate_blog_authors。
        """
        issues: list[ValidationIssueDTO] = []

        required_fields = ["title", "slug", "authors", "tags"]
        for field_name in required_fields:
            if not frontmatter.get(field_name):
                issues.append(
                    ValidationIssueDTO(
                        code=f"blog_{field_name}_missing",
                        message=f"blog 文章缺少 {field_name}。",
                        severity="error",
                    )
                )

        if not frontmatter.get("description"):
            issues.append(
                ValidationIssueDTO(
                    code="blog_description_missing",
                    message="blog 文章建议填写 description。",
                )
            )
        if not frontmatter.get("date"):
            issues.append(
                ValidationIssueDTO(
                    code="blog_date_missing",
                    message="blog 文章建议填写 date。",
                )
            )
        else:
            date_value = self._string_value(frontmatter.get("date"))
            if date_value and not self.date_prefix_pattern.match(date_value):
                issues.append(
                    ValidationIssueDTO(
                        code="blog_date_invalid",
                        message="blog date 必须以 YYYY-MM-DD 开头。",
                        severity="error",
                    )
                )

        # 逐个核对作者是否已在站点 authors.yml 中登记
        for author in self._list_value(frontmatter.get("authors")):
            if author not in known_authors:
                issues.append(
                    ValidationIssueDTO(
                        code="blog_author_unknown",
                        message=f"blog 作者 {author} 不存在于 site/blog/authors.yml。",
                        severity="error",
                    )
                )

        return issues

    def _validate_image_references(self, article_path: Path, body: str) -> list[ValidationIssueDTO]:
        """校验 Markdown/HTML 正文中的文章相对图片引用是否存在。"""
        issues: list[ValidationIssueDTO] = []
        missing_references, out_of_scope_references = self._missing_image_references(article_path, body)

        for source in out_of_scope_references:
            issues.append(
                ValidationIssueDTO(
                    code="image_reference_out_of_scope",
                    message=f"图片引用路径越界：{source}",
                    severity="error",
                )
            )
        for source in missing_references:
            issues.append(
                ValidationIssueDTO(
                    code="image_reference_missing",
                    message=f"图片引用不存在：{source}",
                    severity="error",
                )
            )

        return issues

    def _build_move_target(
        self,
        article_type: ArticleType,
        relative_path: str,
        payload: ArticleMoveDTO,
        parsed: ParsedMarkdown,
    ) -> tuple[str, dict[str, Any]]:
        """根据移动请求生成目标相对路径与执行后 Front Matter。"""
        extension = Path(relative_path).suffix or ".md"
        frontmatter = dict(parsed.frontmatter)

        if article_type == ArticleType.docs:
            self._validate_target_category_path(payload.target_category_path)
            target_relative_path = "/".join([*payload.target_category_path, f"{payload.target_slug}{extension}"])
            return target_relative_path, frontmatter

        if payload.target_category_path:
            raise BadRequestError(
                "blog 文章不能设置 target_category_path。",
                code="invalid_target_category",
                details={"target_category_path": payload.target_category_path},
            )

        date_value = payload.target_date or self._string_value(frontmatter.get("date")) or self._date_prefix_from_path(relative_path)
        date_prefix = self._date_prefix(date_value)
        frontmatter["slug"] = payload.target_slug
        frontmatter["date"] = date_value
        return f"{date_prefix}-{payload.target_slug}{extension}", frontmatter

    def _planned_article_link_replacements(
        self,
        article_type: ArticleType,
        old_relative_path: str,
        new_relative_path: str,
        old_frontmatter: dict[str, Any],
        new_frontmatter: dict[str, Any],
    ) -> dict[str, str]:
        """生成移动文章后可自动替换的站内链接文本映射。"""
        old_slug = self._resolve_slug(article_type, old_relative_path, old_frontmatter)
        new_slug = self._resolve_slug(article_type, new_relative_path, new_frontmatter)
        old_route = self._build_route(article_type, old_slug)
        new_route = self._build_route(article_type, new_slug)

        replacements = {
            old_route: new_route,
            old_route.lstrip("/"): new_route.lstrip("/"),
            old_relative_path: new_relative_path,
            f"./{old_relative_path}": f"./{new_relative_path}",
            f"../{old_relative_path}": f"../{new_relative_path}",
        }
        return {
            old: new
            for old, new in replacements.items()
            if old and new and old != new
        }

    def _find_link_replacement_targets(self, moving_article_path: Path, replacements: dict[str, str]) -> list[Path]:
        """查找包含旧链接文本的其他文章文件。"""
        if not replacements:
            return []

        targets: list[Path] = []
        moving_article_path = moving_article_path.resolve()
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                if path.resolve() == moving_article_path:
                    continue
                content = path.read_text(encoding="utf-8")
                if any(old in content for old in replacements):
                    targets.append(path)
        return targets

    def _replace_article_links(self, moving_article_path: Path, replacements: dict[str, str]) -> None:
        """在其他文章中替换明确匹配到的旧站内链接文本。"""
        for path in self._find_link_replacement_targets(moving_article_path, replacements):
            content = path.read_text(encoding="utf-8")
            updated = content
            for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
                updated = updated.replace(old, new)
            if updated != content:
                path.write_text(updated, encoding="utf-8")

    def _validate_target_category_path(self, category_path: list[str]) -> None:
        """校验 docs 移动目标分类路径；空列表表示 docs 根目录。"""
        invalid_segments = [
            segment
            for segment in category_path
            if not self._is_safe_path_segment(segment)
        ]
        if invalid_segments:
            raise BadRequestError(
                "docs 目标分类片段不合法。",
                code="invalid_target_category",
                details={"target_category_path": category_path, "invalid_segments": invalid_segments},
            )

    @staticmethod
    def _replace_moved_article_image_dir_refs(body: str, old_dir_name: str, new_dir_name: str) -> str:
        """重命名同名图片目录后，同步正文中的文章相对图片目录引用。"""
        if old_dir_name == new_dir_name:
            return body

        replacements = {
            f"./{old_dir_name}/": f"./{new_dir_name}/",
            f"{old_dir_name}/": f"{new_dir_name}/",
        }
        updated = body
        for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            updated = updated.replace(old, new)
        return updated

    def _find_article_references(
        self,
        article_type: ArticleType,
        relative_path: str,
        parsed: ParsedMarkdown,
    ) -> list[str]:
        """扫描其他文章中对待删除文章的显式文本引用。"""
        candidates = self._article_reference_candidates(article_type, relative_path, parsed.frontmatter)
        if not candidates:
            return []

        references: list[str] = []
        for current_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(current_type):
                current_relative_path = self.filesystem.relative_posix_path(current_type, path)
                if current_type == article_type and current_relative_path == relative_path:
                    continue

                content = path.read_text(encoding="utf-8")
                if any(candidate in content for candidate in candidates):
                    references.append(f"{current_type.value}:{current_relative_path}")

        return references

    def _article_reference_candidates(
        self,
        article_type: ArticleType,
        relative_path: str,
        frontmatter: dict[str, Any],
    ) -> set[str]:
        """生成文章删除前用于基础站内引用扫描的候选文本。"""
        candidates = {relative_path, f"./{relative_path}", f"../{relative_path}"}
        if article_type == ArticleType.docs:
            doc_id = self.sidebar.doc_id_from_relative_path(relative_path)
            candidates.update({doc_id, f"/docs/{doc_id}", f"docs/{doc_id}"})
        else:
            slug = self._resolve_slug(article_type, relative_path, frontmatter)
            candidates.update({f"/blog/{slug}", f"blog/{slug}"})

        return {candidate for candidate in candidates if candidate}

    def _missing_image_references(self, article_path: Path, body: str) -> tuple[list[str], list[str]]:
        """返回正文中缺失或越界的本地图片引用。"""
        missing_references: list[str] = []
        out_of_scope_references: list[str] = []
        seen_sources: set[str] = set()

        for source in self._extract_image_sources(body):
            normalized_source = self._normalize_local_image_source(source)
            if not normalized_source or normalized_source in seen_sources:
                continue

            seen_sources.add(normalized_source)
            try:
                target = ensure_child_path(article_path.parent, article_path.parent / normalized_source)
            except PathSecurityError:
                out_of_scope_references.append(source)
                continue

            if not target.exists() or not target.is_file():
                missing_references.append(source)

        return missing_references, out_of_scope_references

    def _referenced_image_source_set(self, body: str) -> set[str]:
        """返回正文中全部本地文章相对图片引用。"""
        sources: set[str] = set()
        for source in self._extract_image_sources(body):
            normalized_source = self._normalize_local_image_source(source)
            if normalized_source:
                sources.add(normalized_source.lstrip("./"))
        return sources

    @staticmethod
    def _is_image_referenced(image_dir_name: str, image_name: str, referenced_sources: set[str]) -> bool:
        """判断图片是否被正文以文章相对路径引用。"""
        candidates = {
            f"{image_dir_name}/{image_name}",
            f"./{image_dir_name}/{image_name}",
            image_name,
            f"./{image_name}",
        }
        normalized_candidates = {candidate.lstrip("./") for candidate in candidates}
        return bool(normalized_candidates & referenced_sources)

    def _scan_image_files(self, image_dir: Path) -> list[Path]:
        """扫描文章图片目录下允许展示的图片文件。"""
        files = [
            path
            for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in self.image_extensions
        ]
        return sorted(files, key=lambda item: item.name.lower())

    def _validate_image_content(self, extension: str, content_type: str | None, content: bytes) -> None:
        """校验图片 MIME 与文件头，SVG 额外检查危险脚本与外链。"""
        normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
        allowed_types = self.image_mime_types.get(extension, set())
        if normalized_type and normalized_type not in allowed_types:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

        if extension == ".svg":
            self._validate_svg_content(content)
            return

        if not self._matches_image_magic(extension, content):
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")

    @staticmethod
    def _matches_image_magic(extension: str, content: bytes) -> bool:
        """根据常见文件头校验二进制图片类型。"""
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
    def _validate_svg_content(content: bytes) -> None:
        """对 SVG 做轻量安全校验，拒绝脚本、事件属性和外部链接。"""
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

    def _build_safe_image_stem(self, value: str) -> str:
        """生成安全图片文件名 stem，保留中文文章名。"""
        normalized = value.strip()
        normalized = re.sub(r"[\s_]+", "-", normalized)
        normalized = self.unsafe_path_segment_pattern.sub("-", normalized)
        normalized = re.sub(r"-+", "-", normalized).strip("-. ")
        if not normalized or normalized in {".", ".."} or ".." in normalized:
            raise BadRequestError("文件名无法生成安全路径片段。", code="invalid_file_name")
        return normalized

    def _validate_image_name(self, image_name: str) -> None:
        """校验待删除图片文件名，拒绝路径片段和不支持的图片扩展名。"""
        if (
            not image_name
            or "/" in image_name
            or "\\" in image_name
            or image_name in {".", ".."}
            or ".." in image_name
            or image_name.rstrip(" .") != image_name
            or not self.image_name_pattern.fullmatch(image_name)
            or Path(image_name).suffix.lower() not in self.image_extensions
        ):
            raise BadRequestError(
                "图片名包含路径分隔符或非法字符。",
                code="invalid_image_name",
                details={"image_name": image_name},
            )

    @staticmethod
    def _next_available_image_path(image_dir: Path, stem: str, extension: str) -> Path:
        """生成不覆盖已有文件的图片路径。"""
        target = image_dir / f"{stem}{extension}"
        if not target.exists():
            return target

        index = 1
        while True:
            candidate = image_dir / f"{stem}-{index}{extension}"
            if not candidate.exists():
                return candidate
            index += 1

    def _extract_image_sources(self, body: str) -> list[str]:
        """提取正文中的 Markdown 图片和 HTML img src。"""
        sources = [match.group("src") for match in self.markdown_image_pattern.finditer(body)]
        sources.extend(match.group("src") for match in self.html_image_pattern.finditer(body))
        return sources

    @staticmethod
    def _normalize_local_image_source(source: str) -> str | None:
        """过滤非本地文章相对图片引用，并移除 query/hash。"""
        cleaned = source.strip().strip("\"'")
        if not cleaned:
            return None

        lower_cleaned = cleaned.lower()
        skipped_prefixes = ("http://", "https://", "data:", "mailto:", "#", "/")
        if lower_cleaned.startswith(skipped_prefixes):
            return None

        without_fragment = cleaned.split("#", 1)[0].split("?", 1)[0].strip()
        return without_fragment.split(maxsplit=1)[0] if without_fragment else None

    def _load_blog_authors(self) -> set[str]:
        """从 site/blog/authors.yml 加载全部合法作者 ID；文件缺失或格式异常时返回空集。"""
        authors_path = settings.blog_dir / "authors.yml"
        if not authors_path.exists():
            return set()

        try:
            loaded = yaml.safe_load(authors_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return set()

        if not isinstance(loaded, dict):
            return set()

        return set(str(author_id) for author_id in loaded.keys())

    def _validate_blog_authors(self, authors: list[str]) -> None:
        """创建 blog 文章前的硬校验：任一作者未登记即抛 BadRequestError。"""
        known_authors = self._load_blog_authors()
        unknown_authors = [author for author in authors if author not in known_authors]
        if unknown_authors:
            raise BadRequestError(
                "blog 作者不存在于 site/blog/authors.yml。",
                code="blog_author_unknown",
                details={"authors": unknown_authors},
            )

    def _validate_slug_segment(self, value: str, *, field_name: str) -> None:
        """校验单个 slug 段格式：仅小写字母/数字/连字符，且以字母或数字开头。"""
        if not self.slug_segment_pattern.fullmatch(value):
            raise BadRequestError(
                "slug 只能使用小写英文、数字和连字符，并且必须以英文或数字开头。",
                code="invalid_slug",
                details={"field": field_name, "value": value},
            )

    def _validate_path_segment(self, value: str, *, field_name: str) -> None:
        """校验文章文件名或 docs 分类目录片段，允许中文但拒绝路径穿越与系统非法字符。"""
        if not self._is_safe_path_segment(value):
            raise BadRequestError(
                "路径片段不能为空，不能使用 . 或 ..，且不能包含 /、\\、:、*、?、\"、<、>、| 等字符。",
                code="invalid_path_segment",
                details={"field": field_name, "value": value},
            )

    def _is_safe_path_segment(self, value: str) -> bool:
        normalized = value.strip()
        return bool(
            normalized
            and normalized not in {".", ".."}
            and not self.unsafe_path_segment_pattern.search(normalized)
            and not normalized.endswith((".", " "))
        )

    def _date_prefix(self, date_value: str) -> str:
        """从 date 中提取 YYYY-MM-DD 前缀用于文件命名；格式不符则抛 BadRequestError。"""
        match = self.date_prefix_pattern.match(date_value)
        if not match:
            raise BadRequestError(
                "blog date 必须以 YYYY-MM-DD 开头。",
                code="invalid_blog_date",
                details={"date": date_value},
            )
        return match.group(0)

    def _date_prefix_from_path(self, relative_path: str) -> str:
        """从 blog 文件名中回退提取 YYYY-MM-DD 日期前缀。"""
        stem = Path(relative_path).stem
        match = self.date_prefix_pattern.match(stem)
        if not match:
            raise BadRequestError(
                "blog date 必须以 YYYY-MM-DD 开头。",
                code="invalid_blog_date",
                details={"relative_path": relative_path},
            )
        return match.group(0)

    @staticmethod
    def _now_shanghai_iso() -> str:
        """返回当前上海时区（Asia/Shanghai）的 ISO 时间字符串（精度到秒）。"""
        return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    def _resolve_slug(
        self,
        article_type: ArticleType,
        relative_path: str,
        frontmatter: dict[str, Any],
    ) -> str:
        """解析文章 slug：docs 固定取 doc_id；blog 依次取 frontmatter.slug、文件名（去除日期前缀）。"""
        if article_type == ArticleType.docs:
            return self.sidebar.doc_id_from_relative_path(relative_path)

        frontmatter_slug = self._string_value(frontmatter.get("slug"))
        if frontmatter_slug:
            return frontmatter_slug

        # 无显式 slug 时回退到文件名，并尝试剥离 YYYY-MM-DD- 前缀
        stem = Path(relative_path).stem
        match = self.date_slug_pattern.match(stem)
        return match.group("slug") if match else stem

    @staticmethod
    def _build_route(article_type: ArticleType, slug: str) -> str:
        """根据类型与 slug 拼接前端访问路由。"""
        if article_type == ArticleType.docs:
            return f"/docs/{slug}"
        return f"/blog/{slug}"

    @staticmethod
    def _category_path(article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> list[str]:
        """提取文章分类路径；docs 来自目录，blog 优先来自 Front Matter category/categories。"""
        if article_type != ArticleType.docs:
            return []
        parts = Path(relative_path).parent.as_posix().split("/")
        return [] if parts == ["."] else parts

    def _category_candidates(self, frontmatter: dict[str, Any]) -> list[str]:
        candidates: list[str] = []
        candidates.extend(self._list_value(frontmatter.get("category")))
        candidates.extend(self._list_value(frontmatter.get("categories")))
        candidates.extend(self._list_value(frontmatter.get("tags")))
        return candidates

    def _matches_filters(
        self,
        summary: ArticleSummaryDTO,
        *,
        keyword: str | None,
        tag: str | None,
        author: str | None,
        category: str | None,
        has_issues: bool | None,
    ) -> bool:
        """聚合列表接口的过滤条件。"""
        if not self._matches_keyword(summary, keyword):
            return False
        if tag and tag not in summary.tags:
            return False
        if author and author not in summary.authors:
            return False
        if category:
            normalized_category = category.strip("/")
            current_category = "/".join(summary.category_path)
            if not current_category.startswith(normalized_category):
                return False
        if has_issues is True and not summary.issues:
            return False
        return True

    @staticmethod
    def _matches_keyword(summary: ArticleSummaryDTO, keyword: str | None) -> bool:
        """关键词命中检测：在标题、描述、路径、slug、标签中做大小写不敏感包含匹配。"""
        if not keyword:
            return True

        normalized = keyword.lower()
        fields = [
            summary.title or "",
            summary.description or "",
            summary.relative_path,
            summary.slug,
            " ".join(summary.tags),
        ]
        return any(normalized in field.lower() for field in fields)

    def _sort_articles(self, articles: list[ArticleSummaryDTO], sort: str | None) -> list[ArticleSummaryDTO]:
        """按文档约定字段排序；字段前缀 '-' 表示倒序，便于前端使用。"""
        if not sort:
            return articles

        descending = sort.startswith("-")
        field_name = sort[1:] if descending else sort
        if field_name not in self.sortable_fields:
            raise BadRequestError("sort 字段不支持。", code="invalid_sort_field", details={"sort": sort})

        return sorted(
            articles,
            key=lambda article: self._article_sort_value(article, field_name),
            reverse=descending,
        )

    @staticmethod
    def _article_sort_value(article: ArticleSummaryDTO, field_name: str) -> str:
        """返回列表排序值。"""
        if field_name == "title":
            return article.title or ""
        if field_name == "date":
            return article.relative_path[:10] if article.type == ArticleType.blog else ""
        if field_name == "updated_at":
            return article.updated_at
        if field_name == "relative_path":
            return article.relative_path
        if field_name == "type":
            return article.type.value
        return ""

    @staticmethod
    def _file_version(path: Path) -> str:
        """基于文件修改时间与大小生成乐观锁版本。"""
        stat = path.stat()
        return f"mtime:{stat.st_mtime_ns}:size:{stat.st_size}"

    @staticmethod
    def _file_updated_at(path: Path) -> str:
        """返回文件最后修改时间的上海时区 ISO 字符串。"""
        return datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    @staticmethod
    def _file_created_at(path: Path) -> str:
        """返回文件创建时间的上海时区 ISO 字符串。"""
        return datetime.fromtimestamp(path.stat().st_ctime, tz=ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    @staticmethod
    def _project_relative_posix_path(path: Path) -> str:
        """返回相对项目根目录的 posix 路径。"""
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _string_value(value: Any) -> str | None:
        """将任意值规范化为字符串，None 透传。"""
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        """将标量或列表统一规整为字符串列表。"""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @staticmethod
    def _encode_article_id(article_type: ArticleType, relative_path: str) -> str:
        """将 type:relative_path 编码为 URL 安全的 base64 字符串作为对外文章 ID。"""
        raw = f"{article_type.value}:{relative_path}"
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_article_id(article_id: str) -> tuple[ArticleType, str]:
        """解码文章 ID 为 (类型, 相对路径)；格式非法时抛 NotFoundError。"""
        # 补齐 base64 缺省的 = 填充位
        padding = "=" * (-len(article_id) % 4)
        try:
            raw = base64.urlsafe_b64decode(f"{article_id}{padding}").decode("utf-8")
            type_text, relative_path = raw.split(":", 1)
            return ArticleType(type_text), relative_path
        except (ValueError, UnicodeDecodeError) as exc:
            raise NotFoundError("文章 ID 无效。", code="article_id_invalid") from exc
