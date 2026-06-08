"""
Front Matter 解析与生成服务
对齐 Node.js 后端的输出格式
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import frontmatter


# ============================================================
# 解析
# ============================================================

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析 Markdown 文件的 Front Matter。

    Returns:
        (front_matter_dict, body_text)
    """
    content = content.lstrip("﻿")  # 去 BOM
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def flatten_categories(raw: Any) -> List[str]:
    """
    将 Front Matter 中的 categories 统一为扁平列表。

    支持以下格式：
      - [技术研习, Vue3]         → ["技术研习", "Vue3"]
      - [[技术研习, Vue3]]        → ["技术研习", "Vue3"]
      - 技术研习                  → ["技术研习"]
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        if len(raw) == 0:
            return []
        # 嵌套数组：[[一级, 二级]]
        if isinstance(raw[0], list):
            return [item for sub in raw for item in sub]
        # 扁平列表：[一级, 二级]
        return list(raw)
    return [str(raw)]


# ============================================================
# 生成
# ============================================================

def _escape_yaml_value(val: str) -> str:
    """如果字符串包含 YAML 特殊字符则加引号"""
    if not val:
        return val
    special = r"""[:#\n\r\t{}[\],&*?|<>=!%@`"]"""
    if re.search(special, val) or val.startswith(" ") or val.endswith(" "):
        return f'"{val}"'
    return val


def generate_frontmatter(data: Dict[str, Any]) -> str:
    """
    将 Front Matter 字典序列化为 YAML 文本（包含 --- 分隔符）。
    输出格式与 Node.js 后端的 generateFrontMatter 完全一致。
    """
    lines: List[str] = ["---"]

    # 基础字段
    if data.get("title"):
        lines.append(f"title: {_escape_yaml_value(str(data['title']))}")
    if data.get("date"):
        lines.append(f"date: {data['date']}")
    if data.get("updated"):
        lines.append(f"updated: {data['updated']}")

    # 分类 —— 使用嵌套数组格式 [[一级, 二级]]
    categories = data.get("categories")
    if categories:
        lines.append("")
        lines.append("categories:")
        if isinstance(categories, list) and len(categories) > 0:
            if isinstance(categories[0], list):
                # 已经是嵌套格式
                for cat in categories:
                    lines.append(f"  - [{', '.join(str(c) for c in cat)}]")
            else:
                # 扁平格式 → 嵌套
                lines.append(f"  - [{', '.join(str(c) for c in categories)}]")

    # 标签
    tags = data.get("tags")
    if tags and len(tags) > 0:
        lines.append("")
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")

    # 可选字段（保持与 Node 后端一致的输出顺序）
    optional_fields = [
        ("description", "description"),
        ("layout", "layout"),
        ("comments", "comments"),
        ("permalink", "permalink"),
        ("excerpt", "excerpt"),
        ("published", "published"),
        ("lang", "lang"),
        ("cover", "cover"),
        ("sticky", "sticky"),
        ("slug", "slug"),
        ("status", "status"),
        ("series", "series"),
    ]
    for key, field_name in optional_fields:
        val = data.get(field_name if key == field_name else field_name)
        if val is not None:
            lines.append("")
            if isinstance(val, str):
                lines.append(f"{field_name}: {_escape_yaml_value(val)}")
            else:
                lines.append(f"{field_name}: {val}")

    # 系列顺序（紧跟 series）
    if data.get("series_order") is not None:
        lines.append(f"series_order: {data['series_order']}")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# 图片相关工具
# ============================================================

def get_asset_folder_path(article_path: str, posts_dir: Path) -> Path:
    """获取文章对应的资源文件夹路径（与文章同名，去掉 .md 扩展名）"""
    return posts_dir / article_path.replace(".md", "")


def get_next_image_number(article_path: str, posts_dir: Path) -> int:
    """获取下一个图片编号（从 1 开始递增）"""
    asset_folder = get_asset_folder_path(article_path, posts_dir)
    if not asset_folder.exists():
        return 1

    max_num = 0
    for f in asset_folder.iterdir():
        if f.is_file() and re.match(r".*img(\d+)\.", f.name, re.IGNORECASE):
            m = re.search(r"img(\d+)", f.name, re.IGNORECASE)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return max_num + 1
