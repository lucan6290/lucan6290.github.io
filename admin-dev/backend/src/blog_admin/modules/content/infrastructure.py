from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.path_security import resolve_under
from ...core.response import fail, ok
from ...core.settings import settings
from ..categories.registry import find_primary_by_prefix, find_secondary_by_prefix


@dataclass(frozen=True)
class HexoPostCreator:
    blog_root: Path = settings.blog_root
    posts_dir: Path = settings.posts_dir
    timeout_seconds: int = 30

    def create(self, title: str, prefix1: str, prefix2: str) -> dict[str, Any]:
        primary = find_primary_by_prefix(prefix1)
        if not primary:
            return fail("POST_CATEGORY_INVALID", f"无效的一级前缀: {prefix1}")
        if not primary.get("enabled", True):
            return fail("POST_CATEGORY_DISABLED", f"一级分类已停用: {primary.get('frontend_name1')}")
        if not prefix2:
            return fail("POST_PREFIX_INVALID", "二级前缀不能为空")
        if "-" in prefix2:
            return fail("POST_PREFIX_INVALID", f"二级前缀(prefix2)不能包含连字符(-)，当前值: {prefix2}")

        category_pair = find_secondary_by_prefix(prefix1, prefix2)
        if not category_pair:
            return fail("POST_CATEGORY_INVALID", f"二级前缀不存在: {prefix1}-{prefix2}，请先在分类管理中添加")
        _primary, secondary = category_pair
        if not secondary.get("enabled", True):
            return fail("POST_CATEGORY_DISABLED", f"二级分类已停用: {secondary.get('frontend_name2')}")

        try:
            result = subprocess.run(
                ["npx", "hexo", "np", prefix1, prefix2, title],
                cwd=str(self.blog_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_seconds,
                shell=True,
            )

            filename = f"{prefix1}-{prefix2}-{title}.md"
            relative = f"{primary['category_slug']}/{filename}"
            file_path = resolve_under(self.posts_dir, relative, label="文章路径")

            if not file_path.exists():
                output = result.stdout.strip()
                if "错误" in output:
                    error_message = output.split("错误:")[-1].strip().split("\n")[0]
                    return fail("POST_CREATE_FAILED", error_message)
                return fail("POST_CREATE_FAILED", f"hexo np 执行失败: {output or result.stderr.strip()}")

            return ok({"path": relative})
        except subprocess.TimeoutExpired:
            return fail("POST_CREATE_TIMEOUT", f"hexo np 执行超时（{self.timeout_seconds}s）")
        except Exception as exc:
            return fail("POST_CREATE_FAILED", f"创建文章失败: {exc}")
