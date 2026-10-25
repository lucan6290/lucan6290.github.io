"""标签 slug 规范化服务。"""

import hashlib
import re


class TagSlugService:
    """提供公开的标签 slug 生成与校验能力。"""

    slug_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*$")

    def slug_from_label(self, label: str) -> str:
        """将标签文本转为安全 slug；中文等文本使用稳定哈希兜底。"""
        normalized = label.strip()
        slug = normalized.lower()
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if slug and self.is_valid_slug(slug):
            return slug

        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
        return f"tag-{digest}"

    def is_valid_slug(self, slug: str) -> bool:
        return bool(self.slug_pattern.fullmatch(slug))
