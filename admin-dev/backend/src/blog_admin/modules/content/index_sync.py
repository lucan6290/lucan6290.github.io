from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ...core.settings import settings
from .frontmatter import flatten_categories
from .index_updater import handle_status_change, parse_index, remove_from_index, update_in_index
from .repository import PostRepository

logger = logging.getLogger(__name__)


class PostIndexSyncService:
    def __init__(
        self,
        index_path: Path = settings.posts_dir / "index.md",
        repository: PostRepository | None = None,
    ) -> None:
        self.index_path = index_path
        self.repository = repository or PostRepository()

    def read_index(self) -> str | None:
        if not self.index_path.exists():
            return None
        return self.index_path.read_text(encoding="utf-8")

    def write_index(self, content: str) -> None:
        if not self.index_path.exists():
            logger.error("目录文件 index.md 不存在，无法写入")
            return

        backup_path = self.index_path.with_suffix(".md.bak")
        backup_path.write_text(self.index_path.read_text(encoding="utf-8"), encoding="utf-8")

        try:
            self.index_path.write_text(content, encoding="utf-8")
            structure = parse_index(content)
            if not structure.categories:
                raise ValueError("写入后验证失败：目录无一级分类")
            backup_path.unlink(missing_ok=True)
            logger.info("index.md 更新成功")
        except Exception:
            logger.exception("index.md 写入验证失败，回滚")
            self.index_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
            backup_path.unlink(missing_ok=True)
            raise

    def sync_on_update(self, existing_fm: dict[str, Any], new_fm: dict[str, Any], filename: str) -> None:
        try:
            index_text = self.read_index()
            if index_text is None:
                return

            old_status = existing_fm.get("status", "draft")
            new_status = new_fm.get("status", old_status)
            old_categories = flatten_categories(existing_fm.get("categories", []))
            new_categories = flatten_categories(new_fm.get("categories", []))
            old_title = existing_fm.get("title", "")
            new_title = new_fm.get("title", "")
            old_date = str(existing_fm.get("date", ""))
            new_date = str(new_fm.get("date", ""))
            primary_name = new_categories[0] if new_categories else ""
            category_slug = self.repository.to_slug(primary_name)

            if old_status != new_status:
                new_index, message = handle_status_change(
                    index_text,
                    title=new_title or old_title,
                    date=new_date or old_date,
                    categories=new_categories or old_categories,
                    filename=filename,
                    category_slug=category_slug,
                    old_status=old_status,
                    new_status=new_status,
                )
                if new_index != index_text:
                    self.write_index(new_index)
                    logger.info("目录同步（状态变更）：%s", message)
                return

            if new_status == "published":
                if old_categories != new_categories or old_title != new_title or old_date != new_date:
                    new_index, message = update_in_index(
                        index_text,
                        old_filename=filename,
                        new_title=new_title or old_title,
                        new_date=new_date or old_date,
                        new_categories=new_categories or old_categories,
                        new_filename=filename,
                        new_category_slug=category_slug,
                    )
                    if new_index != index_text:
                        self.write_index(new_index)
                        logger.info("目录同步（更新）：%s", message)
        except Exception:
            logger.exception("目录同步失败（不影响文章保存）")

    def remove_post(self, filename: str) -> None:
        try:
            index_text = self.read_index()
            if index_text is None:
                return
            new_index, message = remove_from_index(index_text, filename)
            if new_index != index_text:
                self.write_index(new_index)
                logger.info("目录同步（删除）：%s", message)
        except Exception:
            logger.exception("目录同步失败（不影响删除操作）")

