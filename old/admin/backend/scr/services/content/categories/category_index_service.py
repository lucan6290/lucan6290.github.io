"""docs 一级分类目录页维护服务。"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


@dataclass(frozen=True)
class _DocEntry:
    title: str
    link: str


@dataclass(frozen=True)
class _SecondLevelGroup:
    slug: str
    label: str
    docs: list[_DocEntry]


@dataclass(frozen=True)
class _TopLevelGroup:
    slug: str
    label: str
    description: str | None
    direct_docs: list[_DocEntry]
    second_groups: list[_SecondLevelGroup]


class CategoryIndexService:
    """维护 ``site/docs/<top>/index.md`` 作为一级分类目录页。"""

    current_contents_heading = "## 当前内容"
    root_contents_heading = "## 知识库目录"

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()

    def ensure_top_category_index(
        self,
        top_slug: str,
        label: str | None = None,
        description: str | None = None,
    ) -> FileChangeDTO | None:
        """确保一级分类目录页存在；不扫描分类下文章。"""
        top_slug = top_slug.strip()
        if not top_slug:
            return None

        index_path = settings.docs_dir / top_slug / "index.md"
        if index_path.exists():
            return None

        label = label or self._category_label([top_slug])
        description = description or self._category_description([top_slug]) or f"{label}分类目录页。"
        content = self._empty_index_content(label, description)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(content, encoding="utf-8")
        return FileChangeDTO(
            action="create",
            target=self._project_relative_posix_path(index_path),
            description="创建 docs 一级分类目录页",
        )

    def upsert_doc_link(self, relative_path: str, title: str, category_labels: list[str] | None = None) -> FileChangeDTO | None:
        """在一级分类目录页中追加或更新一篇文章链接；不扫描其他文章。"""
        return self.upsert_doc_link_if_index_exists(relative_path, title, category_labels, create_index=True)

    def upsert_doc_link_if_index_exists(
        self,
        relative_path: str,
        title: str,
        category_labels: list[str] | None = None,
        *,
        create_index: bool = False,
    ) -> FileChangeDTO | None:
        """在一级分类目录页中维护文章链接；可选择缺失时不创建目录页。"""
        location = self._doc_location(relative_path)
        if location is None:
            return None

        top_slug, second_slug, link = location
        labels = category_labels or []
        top_label = labels[0] if len(labels) >= 1 and labels[0] else self._category_label([top_slug])
        second_label = labels[1] if len(labels) >= 2 and labels[1] else self._category_label([top_slug, second_slug])
        index_path = settings.docs_dir / top_slug / "index.md"
        if not index_path.exists():
            if not create_index:
                return None
            self.ensure_top_category_index(top_slug, top_label)

        original = index_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(original)
        body = self._ensure_current_contents(parsed.body, top_label)
        updated_body = self._upsert_link_in_body(body, second_label, title, link)
        if updated_body == parsed.body:
            return None

        index_path.write_text(self.markdown.compose(dict(parsed.frontmatter), updated_body), encoding="utf-8")
        return FileChangeDTO(
            action="update",
            target=self._project_relative_posix_path(index_path),
            description="更新 docs 一级分类目录页文章链接",
        )

    def remove_doc_link(self, relative_path: str) -> FileChangeDTO | None:
        """从一级分类目录页中删除一篇文章链接；不扫描其他文章。"""
        location = self._doc_location(relative_path)
        if location is None:
            return None

        top_slug, _second_slug, link = location
        index_path = settings.docs_dir / top_slug / "index.md"
        if not index_path.exists():
            return None

        original = index_path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(original)
        updated_body = self._remove_link_from_body(parsed.body, link)
        if updated_body == parsed.body:
            return None

        index_path.write_text(self.markdown.compose(dict(parsed.frontmatter), updated_body), encoding="utf-8")
        return FileChangeDTO(
            action="update",
            target=self._project_relative_posix_path(index_path),
            description="删除 docs 一级分类目录页文章链接",
        )

    def sync_top_category(self, top_slug: str, *, force: bool = False, dry_run: bool = False) -> FileChangeDTO | None:
        """重建单个一级分类目录页；无内容变化时返回 None。"""
        top_slug = top_slug.strip()
        if not top_slug:
            return None

        index_path = settings.docs_dir / top_slug / "index.md"
        groups = self._groups_for_top_category(top_slug)
        direct_docs = self._direct_docs_for_top_category(top_slug)
        if not groups and not direct_docs and not index_path.exists() and not force:
            return None

        label = self._category_label([top_slug])
        description = self._category_description([top_slug]) or f"{label}分类目录页。"
        desired = self._build_index_content(index_path, label, description, groups, direct_docs)
        action = "update" if index_path.exists() else "create"

        if index_path.exists() and index_path.read_text(encoding="utf-8") == desired:
            return None

        if not dry_run:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(desired, encoding="utf-8")
        return FileChangeDTO(
            action=action,
            target=self._project_relative_posix_path(index_path),
            description=f"{'更新' if action == 'update' else '创建'} docs 一级分类目录页",
        )

    def sync_all(self, *, dry_run: bool = True, confirm: bool = False) -> MutationPlanDTO:
        """遍历 site/docs 一级目录，按真实文章文件重建各自 index.md。"""
        changes: list[FileChangeDTO] = []
        candidates = self._top_category_slugs()
        desired_by_path: dict[Path, str] = {}

        for top_slug in candidates:
            index_path = settings.docs_dir / top_slug / "index.md"
            groups = self._groups_for_top_category(top_slug)
            direct_docs = self._direct_docs_for_top_category(top_slug)
            if not groups and not direct_docs and not index_path.exists():
                continue

            label = self._category_label([top_slug])
            description = self._category_description([top_slug]) or f"{label}分类目录页。"
            desired = self._build_index_content(index_path, label, description, groups, direct_docs)
            action = "update" if index_path.exists() else "create"
            if index_path.exists() and index_path.read_text(encoding="utf-8") == desired:
                continue

            desired_by_path[index_path] = desired
            changes.append(
                FileChangeDTO(
                    action=action,
                    target=self._project_relative_posix_path(index_path),
                    description=f"{'更新' if action == 'update' else '创建'} docs 一级分类目录页",
                )
            )

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=[],
        )
        if dry_run:
            return plan
        if not confirm:
            from scr.core.exceptions import BadRequestError

            raise BadRequestError("同步 docs 分类目录页需要显式确认。", code="confirmation_required")

        for path, content in desired_by_path.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        return plan

    def sync_root_index(self, *, dry_run: bool = False) -> FileChangeDTO | None:
        """重建 ``site/docs/index.md``，作为 docs 全量目录页。"""
        index_path = settings.docs_dir / "index.md"
        groups = self._root_groups()
        desired = self._build_root_index_content(index_path, groups)
        action = "update" if index_path.exists() else "create"

        if index_path.exists() and index_path.read_text(encoding="utf-8") == desired:
            return None

        if not dry_run:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(desired, encoding="utf-8")
        return FileChangeDTO(
            action=action,
            target=self._project_relative_posix_path(index_path),
            description=f"{'更新' if action == 'update' else '创建'} docs 总目录页",
        )

    def _build_index_content(
        self,
        index_path: Path,
        label: str,
        description: str,
        groups: list[_SecondLevelGroup],
        direct_docs: list[_DocEntry] | None = None,
    ) -> str:
        if index_path.exists():
            parsed = self.markdown.parse(index_path.read_text(encoding="utf-8"))
            frontmatter = dict(parsed.frontmatter)
            body_prefix = self._body_prefix_before_current_contents(parsed.body, label)
        else:
            frontmatter = {}
            body_prefix = f"# {label}\n\n这里用于整理{label}下的内容。\n\n"

        frontmatter["title"] = str(frontmatter.get("title") or label)
        frontmatter["description"] = str(frontmatter.get("description") or description)
        frontmatter["sidebar_position"] = int(frontmatter.get("sidebar_position") or 1)

        body = f"{body_prefix.rstrip()}\n\n{self.current_contents_heading}\n"
        for doc in direct_docs or []:
            body += f"\n- [{doc.title}]({doc.link})\n"
        for group in groups:
            body += f"\n## {group.label}\n\n"
            if group.docs:
                body += "\n".join(f"- [{doc.title}]({doc.link})" for doc in group.docs)
                body += "\n"

        return self.markdown.compose(frontmatter, body)

    def _build_root_index_content(self, index_path: Path, groups: list[_TopLevelGroup]) -> str:
        if index_path.exists():
            parsed = self.markdown.parse(index_path.read_text(encoding="utf-8"))
            frontmatter = dict(parsed.frontmatter)
            body_prefix = self._body_prefix_before_marker(parsed.body, self.root_contents_heading, "知识库")
        else:
            frontmatter = {}
            body_prefix = "# 知识库\n\n这里用于整理全部知识库内容。\n\n"

        frontmatter["title"] = str(frontmatter.get("title") or "知识库")
        frontmatter["description"] = str(frontmatter.get("description") or "知识库总目录。")
        frontmatter["sidebar_position"] = int(frontmatter.get("sidebar_position") or 1)

        body = f"{body_prefix.rstrip()}\n\n{self.root_contents_heading}\n"
        for group in groups:
            body += f"\n## [{group.label}](./{group.slug}/)\n"
            if group.description:
                body += f"\n{group.description}\n"
            if group.direct_docs:
                body += "\n"
                body += "\n".join(f"- [{doc.title}]({doc.link})" for doc in group.direct_docs)
                body += "\n"
            for second_group in group.second_groups:
                body += f"\n### {second_group.label}\n\n"
                if second_group.docs:
                    body += "\n".join(f"- [{doc.title}]({doc.link})" for doc in second_group.docs)
                    body += "\n"
        body += "\n"
        return self.markdown.compose(frontmatter, body)

    def _empty_index_content(self, label: str, description: str) -> str:
        frontmatter = {
            "title": label,
            "description": description,
            "sidebar_position": 1,
        }
        body = f"# {label}\n\n这里用于整理{label}下的内容。\n\n{self.current_contents_heading}\n"
        return self.markdown.compose(frontmatter, body)

    def _ensure_current_contents(self, body: str, label: str) -> str:
        normalized = body.replace("\r\n", "\n")
        if self.current_contents_heading in normalized:
            return normalized
        if normalized.strip():
            return f"{normalized.rstrip()}\n\n{self.current_contents_heading}\n"
        return f"# {label}\n\n这里用于整理{label}下的内容。\n\n{self.current_contents_heading}\n"

    def _upsert_link_in_body(self, body: str, second_label: str, title: str, link: str) -> str:
        body = self._ensure_current_contents(body, second_label)
        section = self._find_second_level_section(body, second_label)
        link_line = f"- [{title}]({link})"
        link_pattern = re.compile(rf"^[ \t]*- \[[^\]\n]*\]\({re.escape(link)}\)[ \t]*$", re.MULTILINE)
        if link_pattern.search(body):
            return link_pattern.sub(link_line, body, count=1)

        if section is None:
            return f"{body.rstrip()}\n\n## {second_label}\n\n{link_line}\n"

        start, end = section
        section_text = body[start:end]
        insertion = f"\n{link_line}"
        if section_text.rstrip().endswith(f"## {second_label}"):
            insertion = f"\n\n{link_line}"
        updated_section = f"{section_text.rstrip()}{insertion}\n"
        return body[:start] + updated_section + body[end:]

    def _remove_link_from_body(self, body: str, link: str) -> str:
        section = self._find_section_containing_link(body, link)
        if section is None:
            return body

        start, end = section
        section_text = body[start:end]
        link_pattern = re.compile(rf"^[ \t]*- \[[^\]\n]*\]\({re.escape(link)}\)[ \t]*(?:\n|$)", re.MULTILINE)
        updated_section = link_pattern.sub("", section_text, count=1)
        if not re.search(r"^[ \t]*- ", updated_section, re.MULTILINE):
            return f"{body[:start].rstrip()}\n\n{body[end:].lstrip()}"
        return body[:start] + updated_section.rstrip() + "\n" + body[end:]

    def _find_second_level_section(self, body: str, label: str) -> tuple[int, int] | None:
        pattern = re.compile(rf"^## {re.escape(label)}[ \t]*$", re.MULTILINE)
        match = pattern.search(body)
        if not match:
            return None
        next_match = re.search(r"^## .+$", body[match.end() :], re.MULTILINE)
        end = match.end() + next_match.start() if next_match else len(body)
        return match.start(), end

    def _find_section_containing_link(self, body: str, link: str) -> tuple[int, int] | None:
        link_match = re.search(rf"^[ \t]*- \[[^\]\n]*\]\({re.escape(link)}\)[ \t]*$", body, re.MULTILINE)
        if not link_match:
            return None
        heading_start = body.rfind("\n## ", 0, link_match.start())
        if heading_start == -1:
            heading_start = body.find("## ")
            if heading_start == -1 or heading_start > link_match.start():
                return None
        else:
            heading_start += 1
        next_match = re.search(r"^## .+$", body[link_match.end() :], re.MULTILINE)
        end = link_match.end() + next_match.start() if next_match else len(body)
        return heading_start, end

    @staticmethod
    def _doc_location(relative_path: str) -> tuple[str, str, str] | None:
        parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
        if len(parts) < 3:
            return None
        filename = parts[-1]
        if filename.lower() in {"index.md", "index.mdx"}:
            return None
        top_slug = parts[0]
        second_slug = parts[1]
        link = f"./{'/'.join(parts[1:])}"
        return top_slug, second_slug, link

    def _groups_for_top_category(self, top_slug: str) -> list[_SecondLevelGroup]:
        top_dir = settings.docs_dir / top_slug
        if not top_dir.exists() or not top_dir.is_dir():
            return []

        groups: list[_SecondLevelGroup] = []
        for second_dir in sorted((path for path in top_dir.iterdir() if path.is_dir()), key=lambda item: item.name):
            docs = [
                self._doc_entry(top_slug, path)
                for path in sorted(second_dir.rglob("*"), key=lambda item: item.relative_to(second_dir).as_posix())
                if path.is_file()
                and path.suffix.lower() in self.filesystem.content_extensions
                and path.name.lower() != "index.md"
            ]
            if not docs:
                continue
            second_slug = second_dir.name
            groups.append(
                _SecondLevelGroup(
                    slug=second_slug,
                    label=self._category_label([top_slug, second_slug]),
                    docs=docs,
                )
            )
        return groups

    def _direct_docs_for_top_category(self, top_slug: str) -> list[_DocEntry]:
        top_dir = settings.docs_dir / top_slug
        if not top_dir.exists() or not top_dir.is_dir():
            return []
        return [
            self._doc_entry(top_slug, path)
            for path in sorted(top_dir.iterdir(), key=lambda item: item.name)
            if path.is_file()
            and path.suffix.lower() in self.filesystem.content_extensions
            and path.name.lower() != "index.md"
        ]

    def _root_groups(self) -> list[_TopLevelGroup]:
        groups: list[_TopLevelGroup] = []
        for top_slug in self._top_category_slugs():
            second_groups = self._groups_for_top_category(top_slug)
            direct_docs = self._direct_docs_for_top_category(top_slug)
            groups.append(
                _TopLevelGroup(
                    slug=top_slug,
                    label=self._category_label([top_slug]),
                    description=self._category_description([top_slug]),
                    direct_docs=[
                        _DocEntry(
                            title=doc.title,
                            link=f"./{top_slug}/{doc.link.removeprefix('./')}",
                        )
                        for doc in direct_docs
                    ],
                    second_groups=[
                        _SecondLevelGroup(
                            slug=second.slug,
                            label=second.label,
                            docs=[
                                _DocEntry(
                                    title=doc.title,
                                    link=f"./{top_slug}/{doc.link.removeprefix('./')}",
                                )
                                for doc in second.docs
                            ],
                        )
                        for second in second_groups
                    ],
                )
            )
        return groups

    def _doc_entry(self, top_slug: str, path: Path) -> _DocEntry:
        raw = path.read_text(encoding="utf-8")
        parsed = self.markdown.parse(raw)
        title = str(parsed.frontmatter.get("title") or path.stem)
        relative_to_top = path.relative_to(settings.docs_dir / top_slug).as_posix()
        return _DocEntry(title=title, link=f"./{relative_to_top}")

    def _top_category_slugs(self) -> list[str]:
        if not settings.docs_dir.exists():
            return []
        return sorted(path.name for path in settings.docs_dir.iterdir() if path.is_dir())

    def _body_prefix_before_current_contents(self, body: str, label: str) -> str:
        return self._body_prefix_before_marker(body, self.current_contents_heading, label)

    def _body_prefix_before_marker(self, body: str, marker: str, label: str) -> str:
        normalized = body.replace("\r\n", "\n")
        marker_index = normalized.find(marker)
        if marker_index >= 0:
            return normalized[:marker_index]
        if normalized.strip():
            return normalized.rstrip() + "\n\n"
        return f"# {label}\n\n这里用于整理{label}下的内容。\n\n"

    def _category_label(self, path: list[str]) -> str:
        entry = self._category_entry(path)
        if entry and entry.get("label"):
            return str(entry["label"])
        return self._default_label(path[-1])

    def _category_description(self, path: list[str]) -> str | None:
        entry = self._category_entry(path)
        value = entry.get("description") if entry else None
        text = str(value).strip() if value is not None else ""
        return text or None

    def _category_entry(self, path: list[str]) -> dict[str, Any] | None:
        for entry in self._load_category_entries():
            if str(entry.get("type", ArticleType.docs.value)) != ArticleType.docs.value:
                continue
            if self._entry_path(entry) == path:
                return entry
        return None

    def _load_category_entries(self) -> list[dict[str, Any]]:
        registry_path = settings.content_schema_dir / "categories.yml"
        if not registry_path.exists():
            return []
        loaded = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        entries = loaded.get("categories", [])
        return [entry for entry in entries if isinstance(entry, dict)]

    @staticmethod
    def _entry_path(entry: dict[str, Any]) -> list[str]:
        value = entry.get("path")
        if isinstance(value, list):
            return [str(part).strip() for part in value if str(part).strip()]
        slug = str(entry.get("slug", "")).strip()
        return [slug] if slug else []

    @staticmethod
    def _default_label(slug: str) -> str:
        return slug.replace("-", " ").title()

    @staticmethod
    def _project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
