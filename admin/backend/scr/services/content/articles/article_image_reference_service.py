"""Article image reference parsing and validation."""

from __future__ import annotations

from pathlib import Path
import re

from scr.core.security import PathSecurityError, ensure_child_path
from scr.schemas.article import ValidationIssueDTO


class ArticleImageReferenceService:
    """Parse and validate local image references in article bodies."""

    markdown_image_pattern = re.compile(r"!\[[^\]]*\]\((?P<src>[^)]+)\)")
    html_image_pattern = re.compile(r"<img\b[^>]*\bsrc=[\"'](?P<src>[^\"']+)[\"']", re.IGNORECASE)

    def validate_references(self, article_path: Path, body: str) -> list[ValidationIssueDTO]:
        issues: list[ValidationIssueDTO] = []
        missing_references, out_of_scope_references = self.missing_references(article_path, body)

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

    def missing_references(self, article_path: Path, body: str) -> tuple[list[str], list[str]]:
        missing_references: list[str] = []
        out_of_scope_references: list[str] = []
        seen_sources: set[str] = set()

        for source in self.extract_sources(body):
            normalized_source = self.normalize_local_source(source)
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

    def referenced_source_set(self, body: str) -> set[str]:
        sources: set[str] = set()
        for source in self.extract_sources(body):
            normalized_source = self.normalize_local_source(source)
            if normalized_source:
                sources.add(normalized_source.lstrip("./"))
        return sources

    @staticmethod
    def is_referenced(image_dir_name: str, image_name: str, referenced_sources: set[str]) -> bool:
        candidates = {
            f"{image_dir_name}/{image_name}",
            f"./{image_dir_name}/{image_name}",
            image_name,
            f"./{image_name}",
        }
        normalized_candidates = {candidate.lstrip("./") for candidate in candidates}
        return bool(normalized_candidates & referenced_sources)

    def extract_sources(self, body: str) -> list[str]:
        sources = [match.group("src") for match in self.markdown_image_pattern.finditer(body)]
        sources.extend(match.group("src") for match in self.html_image_pattern.finditer(body))
        return sources

    @staticmethod
    def normalize_local_source(source: str) -> str | None:
        cleaned = source.strip().strip("\"'")
        if not cleaned:
            return None

        lower_cleaned = cleaned.lower()
        skipped_prefixes = ("http://", "https://", "data:", "mailto:", "#", "/")
        if lower_cleaned.startswith(skipped_prefixes):
            return None

        without_fragment = cleaned.split("#", 1)[0].split("?", 1)[0].strip()
        return without_fragment.split(maxsplit=1)[0] if without_fragment else None
