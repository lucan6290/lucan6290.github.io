"""
文章 CRUD 路由
GET/POST/PUT/DELETE /api/files/post(s)
"""
from __future__ import annotations

import logging
import shutil
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
from ..services.index_updater import (
    add_to_index,
    handle_status_change,
    remove_from_index,
    update_in_index,
)

logger = logging.getLogger(__name__)

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
# index.md 自动更新
# ============================================================

INDEX_MD = POSTS_DIR / "index.md"


def _read_index() -> str | None:
    """读取 index.md 内容，失败返回 None"""
    if not INDEX_MD.exists():
        return None
    return INDEX_MD.read_text(encoding="utf-8")


def _write_index(content: str) -> None:
    """写入 index.md（写前备份，写后验证，确认后删除备份）"""
    if not INDEX_MD.exists():
        logger.error("目录文件 index.md 不存在，无法写入")
        return

    # 写前备份
    bak_path = INDEX_MD.with_suffix(".md.bak")
    bak_path.write_text(INDEX_MD.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        # 写入新内容
        INDEX_MD.write_text(content, encoding="utf-8")

        # 写后验证：能解析出至少 1 个一级分类
        from ..services.index_updater import parse_index
        structure = parse_index(content)
        if not structure.categories:
            raise ValueError("写入后验证失败：目录无一级分类")

        # 验证通过，删除备份
        bak_path.unlink(missing_ok=True)
        logger.info("index.md 更新成功")

    except Exception as e:
        # 验证失败，回滚
        logger.error(f"index.md 写入验证失败，回滚：{e}")
        INDEX_MD.write_text(bak_path.read_text(encoding="utf-8"), encoding="utf-8")
        bak_path.unlink(missing_ok=True)
        raise


def _sync_index_on_update(
    existing_fm: Dict[str, Any],
    new_fm: Dict[str, Any],
    filename: str,
) -> None:
    """更新文章后同步 index.md（失败不影响文章保存）"""
    try:
        index_text = _read_index()
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

        # 获取 category_slug
        primary_name = new_categories[0] if new_categories else ""
        category_slug = _to_slug(primary_name)

        # 状态变更处理
        if old_status != new_status:
            new_index, msg = handle_status_change(
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
                _write_index(new_index)
                logger.info(f"目录同步（状态变更）：{msg}")
            return

        # 已发布文章的标题/日期/分类变更
        if new_status == "published":
            old_primary = flatten_categories(existing_fm.get("categories", []))
            category_changed = old_categories != new_categories
            title_changed = old_title != new_title
            date_changed = old_date != new_date

            if category_changed or title_changed or date_changed:
                new_index, msg = update_in_index(
                    index_text,
                    old_filename=filename,
                    new_title=new_title or old_title,
                    new_date=new_date or old_date,
                    new_categories=new_categories or old_categories,
                    new_filename=filename,
                    new_category_slug=category_slug,
                )
                if new_index != index_text:
                    _write_index(new_index)
                    logger.info(f"目录同步（更新）：{msg}")

    except Exception as e:
        logger.error(f"目录同步失败（不影响文章保存）：{e}")


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

        # 同步 index.md（失败不影响文章保存）
        filename = Path(path).stem
        _sync_index_on_update(
            existing_fm=parse_frontmatter(existing)[0],
            new_fm=existing_fm,
            filename=filename,
        )

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
        # 从目录移除（在删除文件之前）
        filename = Path(path).stem
        try:
            index_text = _read_index()
            if index_text is not None:
                new_index, msg = remove_from_index(index_text, filename)
                if new_index != index_text:
                    _write_index(new_index)
                    logger.info(f"目录同步（删除）：{msg}")
        except Exception as e:
            logger.error(f"目录同步失败（不影响删除操作）：{e}")

        # 删除 Markdown 文件
        full_path.unlink()

        # 删除资源文件夹
        asset_folder = full_path.with_suffix("")
        if asset_folder.exists() and asset_folder.is_dir():
            shutil.rmtree(asset_folder, ignore_errors=True)

        return {"success": True, "data": {"path": path}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文章失败: {e}")
