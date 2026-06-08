"""
文章 CRUD 路由
GET/POST/PUT/DELETE /api/files/post(s)
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException

from ..config import BLOG_ROOT, POSTS_DIR, PREFIX_TO_DIR
from ..schemas import (
    CreatePostRequest,
    PostStatus,
    UpdatePostRequest,
)
from ..services.frontmatter import (
    flatten_categories,
    generate_frontmatter,
    parse_frontmatter,
)

router = APIRouter(prefix="/api/files", tags=["文件管理"])


# ============================================================
# 分类名映射（中文 → 英文 slug）
# ============================================================

def _load_category_map() -> Dict[str, str]:
    """从 _config.yml 加载 category_map（中文 → 英文 slug）"""
    try:
        config_path = BLOG_ROOT / "_config.yml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("category_map", {})
    except Exception:
        return {}

CATEGORY_MAP: Dict[str, str] = _load_category_map()


def _to_slug(name: str) -> str:
    """中文分类名 → 英文 slug"""
    return CATEGORY_MAP.get(name, name)


# ============================================================
# 工具函数
# ============================================================

def _safe_get(data: dict, key: str, default: Any = None) -> Any:
    """安全取值，YAML 解析出的 None 视为 default"""
    val = data.get(key, default)
    return default if val is None else val


def _get_markdown_files(directory: Path, base: Path = POSTS_DIR) -> List[str]:
    """递归获取目录下所有 .md 文件（相对于 base 的路径）"""
    results: List[str] = []
    if not directory.exists():
        return results

    for item in sorted(directory.iterdir()):
        if item.is_dir():
            # 跳过资源文件夹（与 .md 同名的文件夹）
            if not item.with_suffix(".md").exists():
                results.extend(_get_markdown_files(item, base))
        elif item.suffix == ".md":
            results.append(item.relative_to(base).as_posix())
    return results


def _parse_post(relative_path: str) -> Optional[Dict]:
    """解析单篇文章的 Front Matter，返回可 JSON 序列化的字典"""
    full_path = POSTS_DIR / relative_path
    if not full_path.exists():
        return None

    content = full_path.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(content)
    categories = flatten_categories(_safe_get(fm, "categories", []))
    tags = _safe_get(fm, "tags", []) or []
    status_val = _safe_get(fm, "status", PostStatus.PUBLISHED)

    # 一级分类 slug（用于前端分类树匹配）
    primary_slug = _to_slug(categories[0]) if categories else ""
    # 二级分类 slug
    sub_slug = _to_slug(categories[1]) if len(categories) > 1 else ""

    return {
        "title": _safe_get(fm, "title", ""),
        "filename": Path(relative_path).stem,
        "path": relative_path.replace("\\", "/"),
        "date": str(_safe_get(fm, "date", "")),
        "updated": _safe_get(fm, "updated"),
        "category": primary_slug,
        "subCategory": sub_slug,
        "categories": categories,
        "tags": tags if isinstance(tags, list) else [],
        "description": _safe_get(fm, "description"),
        "cover": _safe_get(fm, "cover"),
        "status": status_val if status_val in ("draft", "wip", "published") else PostStatus.PUBLISHED,
        "series": _safe_get(fm, "series"),
        "seriesOrder": _safe_get(fm, "series_order"),
    }


# ============================================================
# 路由
# ============================================================

@router.get("/posts")
async def list_posts():
    """获取所有文章列表（按日期倒序）"""
    try:
        files = _get_markdown_files(POSTS_DIR)
        posts: List[dict] = []
        for f in files:
            post = _parse_post(f)
            if post:
                posts.append(post)

        posts.sort(key=lambda p: p.get("date", ""), reverse=True)
        return {"success": True, "data": posts}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取文章列表失败: {e}")


@router.get("/post/{path:path}")
async def get_post(path: str):
    """读取单个文章内容"""
    full_path = POSTS_DIR / path
    if not full_path.exists():
        return {"success": False, "error": "文章不存在"}

    try:
        content = full_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        return {"success": True, "data": {
            "frontMatter": fm,
            "content": content,   # 完整 Markdown（含 Front Matter），供编辑器解析
            "raw": content,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文章失败: {e}")


@router.post("/post")
async def create_post(req: CreatePostRequest):
    """创建新文章（调用 hexo np 命令，只需 title/prefix1/prefix2）"""
    if req.prefix1 not in PREFIX_TO_DIR:
        valid = ", ".join(PREFIX_TO_DIR.keys())
        return {"success": False, "error": f"无效的一级前缀: {req.prefix1}，可用: {valid}"}

    if "-" in req.prefix2:
        return {"success": False, "error": f"二级前缀(prefix2)不能包含连字符(-)，当前值: {req.prefix2}"}

    try:
        # 调用 hexo np <prefix1> <prefix2> "title"
        result = subprocess.run(
            ["npx", "hexo", "np", req.prefix1, req.prefix2, req.title],
            cwd=str(BLOG_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            shell=True,
        )

        # 计算预期文件路径
        config = PREFIX_TO_DIR[req.prefix1]
        filename = f"{req.prefix1}-{req.prefix2}-{req.title}.md"
        relative = f"{config['dir']}/{filename}"
        file_path = POSTS_DIR / relative

        # hexo np 内部用 console.log 输出错误（不抛异常），通过文件是否存在判断
        if not file_path.exists():
            output = result.stdout.strip()
            if "错误" in output:
                error_msg = output.split("错误:")[-1].strip().split("\n")[0]
                return {"success": False, "error": error_msg}
            return {"success": False, "error": f"hexo np 执行失败: {output or result.stderr.strip()}"}

        return {"success": True, "data": {"path": relative}}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "hexo np 执行超时（30s）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建文章失败: {e}")


@router.put("/post/{path:path}")
async def update_post(path: str, req: UpdatePostRequest):
    """更新文章内容"""
    full_path = POSTS_DIR / path
    if not full_path.exists():
        return {"success": False, "error": "文章不存在"}

    try:
        # 读取现有内容
        existing = full_path.read_text(encoding="utf-8")
        existing_fm, _ = parse_frontmatter(existing)

        # 合并 Front Matter
        if req.frontMatter:
            existing_fm.update(req.frontMatter)

        # 自动更新 updated 时间
        existing_fm["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 生成新内容
        new_fm_text = generate_frontmatter(existing_fm)
        new_content = new_fm_text + (req.content or "")

        full_path.write_text(new_content, encoding="utf-8")
        return {"success": True, "data": {"path": path}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文章失败: {e}")


@router.delete("/post/{path:path}")
async def delete_post(path: str):
    """删除文章（同时删除同名资源文件夹）"""
    full_path = POSTS_DIR / path
    if not full_path.exists():
        return {"success": False, "error": "文章不存在"}

    try:
        # 删除 Markdown 文件
        full_path.unlink()

        # 删除资源文件夹
        asset_folder = full_path.with_suffix("")
        if asset_folder.exists() and asset_folder.is_dir():
            import shutil
            shutil.rmtree(asset_folder, ignore_errors=True)

        return {"success": True, "data": {"path": path}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文章失败: {e}")
