from __future__ import annotations

import json
import re
from copy import deepcopy
from html import escape
from typing import Any

from ...core.settings import settings

PREFIX_TO_DIR: dict[str, dict[str, str]] = {
    "ts": {"dir": "tech-study", "category": "技术研习", "cover": "/img/covers/tech-study.svg"},
    "pr": {"dir": "pitfall-review", "category": "踩坑复盘", "cover": "/img/covers/pitfall-review.svg"},
    "pp": {"dir": "project-practice", "category": "项目实战", "cover": "/img/covers/project-practice.svg"},
    "ge": {"dir": "growth-essay", "category": "成长随笔", "cover": "/img/covers/growth-essay.svg"},
    "rs": {"dir": "resource-sharing", "category": "资源分享", "cover": "/img/covers/resource-sharing.svg"},
}


def _default_registry() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, (prefix, config) in enumerate(PREFIX_TO_DIR.items(), start=1):
        items.append(
            {
                "frontend_name1": config["category"],
                "category_slug": config["dir"],
                "note_prefix1": prefix,
                "cover": config["cover"],
                "sort_order": index * 10,
                "enabled": True,
                "children": [],
            }
        )
    return items


def _sort_registry(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_registry = sorted(
        registry,
        key=lambda item: (item.get("sort_order", 9999), item.get("frontend_name1", "")),
    )
    for item in sorted_registry:
        item["children"] = sorted(
            item.get("children") or [],
            key=lambda child: (child.get("sort_order", 9999), child.get("frontend_name2", "")),
        )
    return sorted_registry


def _with_compat_fields(item: dict[str, Any]) -> dict[str, Any]:
    next_item = dict(item)
    next_item["prefix1"] = next_item.get("note_prefix1", "")
    next_item["primaryName"] = next_item.get("frontend_name1", "")
    next_item["primarySlug"] = next_item.get("category_slug", "")
    next_item["dir"] = next_item.get("category_slug", "")
    return next_item


def load_category_registry(*, include_compat: bool = False) -> list[dict[str, Any]]:
    if not settings.category_registry_path.exists():
        registry = _default_registry()
        save_category_registry(registry)
    else:
        registry = json.loads(settings.category_registry_path.read_text(encoding="utf-8"))

    registry = normalize_category_registry(registry)
    if include_compat:
        return [_with_compat_fields(item) for item in registry]
    return registry


def save_category_registry(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = normalize_category_registry(registry)
    settings.category_registry_path.parent.mkdir(parents=True, exist_ok=True)
    settings.category_registry_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ensure_primary_category_assets(normalized)
    return normalized


def normalize_category_registry(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(registry, start=1):
        item = deepcopy(raw)
        item["frontend_name1"] = str(
            item.get("frontend_name1") or item.get("primaryName") or item.get("name") or ""
        ).strip()
        item["category_slug"] = str(
            item.get("category_slug") or item.get("primarySlug") or item.get("dir") or ""
        ).strip()
        item["note_prefix1"] = str(
            item.get("note_prefix1") or item.get("prefix1") or item.get("prefix") or ""
        ).strip()
        default_cover = f"/img/covers/{item['category_slug']}.svg" if item["category_slug"] else ""
        item["cover"] = str(item.get("cover") or default_cover).strip()
        item["sort_order"] = int(item.get("sort_order") or index * 10)
        item["enabled"] = bool(item.get("enabled", True))

        children = []
        for child_index, raw_child in enumerate(item.get("children") or [], start=1):
            child = deepcopy(raw_child)
            child["frontend_name2"] = str(
                child.get("frontend_name2") or child.get("name") or child.get("secondaryName") or ""
            ).strip()
            child["note_prefix2"] = str(
                child.get("note_prefix2") or child.get("prefix2") or child.get("prefix") or ""
            ).strip()
            child["sort_order"] = int(child.get("sort_order") or child_index * 10)
            child["enabled"] = bool(child.get("enabled", True))
            children.append(child)
        item["children"] = children

        for key in ("name", "prefix", "prefix1", "primaryName", "primarySlug", "dir"):
            item.pop(key, None)
        for child in item["children"]:
            for key in ("name", "prefix", "prefix2", "secondaryName"):
                child.pop(key, None)
        normalized.append(item)
    return _sort_registry(normalized)


def validate_category_registry(registry: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen_names: set[str] = set()
    seen_prefix1: set[str] = set()
    seen_slugs: set[str] = set()

    for item in normalize_category_registry(registry):
        name1 = item.get("frontend_name1")
        slug = item.get("category_slug")
        prefix1 = item.get("note_prefix1")
        if not name1:
            errors.append("一级分类 frontend_name1 不能为空")
        elif name1 in seen_names:
            errors.append(f"frontend_name1 重复: {name1}")
        seen_names.add(name1)
        if not slug:
            errors.append(f"一级分类 {name1 or ''} 的 category_slug 不能为空")
        elif not re.fullmatch(r"[A-Za-z0-9_-]+", slug):
            errors.append(f"一级分类 {name1} 的 category_slug 只能使用英文、数字、中划线或下划线")
        if not prefix1:
            errors.append(f"一级分类 {name1 or ''} 的 note_prefix1 不能为空")
        elif not re.fullmatch(r"[A-Za-z0-9_]+", prefix1):
            errors.append(f"一级分类 {name1} 的 note_prefix1 只能使用英文、数字或下划线")
        if slug in seen_slugs:
            errors.append(f"category_slug 重复: {slug}")
        seen_slugs.add(slug)
        if prefix1 in seen_prefix1:
            errors.append(f"note_prefix1 重复: {prefix1}")
        seen_prefix1.add(prefix1)

        seen_prefix2: set[str] = set()
        for child in item.get("children") or []:
            name2 = child.get("frontend_name2")
            prefix2 = child.get("note_prefix2")
            if not name2:
                errors.append(f"{name1} 下存在空 frontend_name2")
            if not prefix2:
                errors.append(f"{name1} / {name2 or ''} 的 note_prefix2 不能为空")
            elif not re.fullmatch(r"[A-Za-z0-9_]+", prefix2):
                errors.append(f"{name1} / {name2} 的 note_prefix2 只能使用英文、数字或下划线")
            if prefix2 in seen_prefix2:
                errors.append(f"{name1} 下 note_prefix2 重复: {prefix2}")
            seen_prefix2.add(prefix2)

    return errors


def ensure_primary_category_assets(registry: list[dict[str, Any]]) -> None:
    for item in registry:
        name = str(item.get("frontend_name1") or "").strip()
        slug = str(item.get("category_slug") or "").strip()
        cover = str(item.get("cover") or f"/img/covers/{slug}.svg").strip()
        if not name or not slug:
            continue
        _ensure_posts_directory(slug)
        _ensure_cover_file(name, slug, cover)
        _ensure_category_map_entry(name, slug)
        _ensure_index_section(name)


def _ensure_posts_directory(slug: str) -> None:
    (settings.posts_dir / slug).mkdir(parents=True, exist_ok=True)


def _ensure_cover_file(name: str, slug: str, cover: str) -> None:
    if not cover.startswith("/img/covers/") or not cover.endswith(".svg"):
        return

    relative_cover = cover.removeprefix("/img/covers/")
    if not re.fullmatch(r"[A-Za-z0-9_\-/]+\.svg", relative_cover):
        return

    cover_path = settings.blog_root / "source" / "img" / "covers" / relative_cover
    covers_root = settings.blog_root / "source" / "img" / "covers"
    try:
        cover_path.resolve().relative_to(covers_root.resolve())
    except ValueError:
        return
    if cover_path.exists():
        return

    cover_path.parent.mkdir(parents=True, exist_ok=True)
    cover_path.write_text(_render_default_cover_svg(name, slug), encoding="utf-8")


def _render_default_cover_svg(name: str, slug: str) -> str:
    safe_name = escape(name)
    safe_slug = escape(slug)
    first_char = escape(name[:1] or "#")
    return f"""<svg width="800" height="450" viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#102a43"/>
      <stop offset="55%" style="stop-color:#243b53"/>
      <stop offset="100%" style="stop-color:#334e68"/>
    </linearGradient>
    <linearGradient id="line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#38b2ac;stop-opacity:0"/>
      <stop offset="50%" style="stop-color:#38b2ac"/>
      <stop offset="100%" style="stop-color:#38b2ac;stop-opacity:0"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <g stroke="#38b2ac" stroke-width="1" opacity="0.08">
    <line x1="70" y1="0" x2="70" y2="450"/>
    <line x1="210" y1="0" x2="210" y2="450"/>
    <line x1="350" y1="0" x2="350" y2="450"/>
    <line x1="490" y1="0" x2="490" y2="450"/>
    <line x1="630" y1="0" x2="630" y2="450"/>
    <line x1="0" y1="90" x2="800" y2="90"/>
    <line x1="0" y1="180" x2="800" y2="180"/>
    <line x1="0" y1="270" x2="800" y2="270"/>
    <line x1="0" y1="360" x2="800" y2="360"/>
  </g>
  <text x="400" y="310" text-anchor="middle" font-family="serif" font-size="260" font-weight="700" fill="#38b2ac" opacity="0.14" filter="url(#glow)">{first_char}</text>
  <text x="400" y="218" text-anchor="middle" font-family="serif" font-size="54" font-weight="700" fill="#9ae6b4" filter="url(#glow)">{safe_name}</text>
  <text x="400" y="258" text-anchor="middle" font-family="'Fira Code',Consolas,monospace" font-size="14" fill="#81e6d9" opacity="0.72">// {safe_slug}</text>
  <path d="M-20 340 Q110 312 220 338 T440 320 T660 342 T820 322" fill="none" stroke="url(#line)" stroke-width="2.5" filter="url(#glow)"/>
  <path d="M-20 365 Q120 340 240 360 T470 344 T690 366 T820 350" fill="none" stroke="url(#line)" stroke-width="1.5" opacity="0.58"/>
  <text x="20" y="435" font-family="'Fira Code',Consolas,monospace" font-size="10" fill="#81e6d9" opacity="0.28">{safe_slug}</text>
</svg>
"""


def _ensure_category_map_entry(name: str, slug: str) -> None:
    config_path = settings.blog_root / "_config.yml"
    if not config_path.exists():
        return

    original_text = config_path.read_text(encoding="utf-8")
    text = original_text
    text = text.replace("一级分类（5个，保持稳定）：技术研习、踩坑复盘、项目实战、成长随笔、资源分享", "一级分类：通过管理端分类管理维护")
    lines = text.splitlines(keepends=True)
    entry_pattern = re.compile(rf"^(\s*){re.escape(name)}\s*:\s*.*$")
    next_entry = f"  {name}: {slug}\n"
    changed = text != original_text

    for index, line in enumerate(lines):
        if entry_pattern.match(line):
            if line != next_entry:
                lines[index] = next_entry
                changed = True
            if changed:
                config_path.write_text("".join(lines), encoding="utf-8")
            return

    insert_at = _find_primary_category_map_insert_index(lines)
    if insert_at is None:
        if changed:
            config_path.write_text("".join(lines), encoding="utf-8")
        return
    lines.insert(insert_at, next_entry)
    config_path.write_text("".join(lines), encoding="utf-8")


def _find_primary_category_map_insert_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if "# 技术研习 - 二级分类" in line:
            insert_at = index
            while insert_at > 0 and (
                lines[insert_at - 1].strip() == "" or lines[insert_at - 1].lstrip().startswith("#")
            ):
                insert_at -= 1
            return insert_at
    for index, line in enumerate(lines):
        if line.strip() == "tag_map:":
            return index
    return None


def _ensure_index_section(name: str) -> None:
    index_path = settings.posts_dir / "index.md"
    if not index_path.exists():
        return

    text = index_path.read_text(encoding="utf-8")
    if re.search(rf"^##\s+(?:[一二三四五六七八九十]+、)?{re.escape(name)}\s*$", text, flags=re.MULTILINE):
        return

    section_count = len(re.findall(r"^##\s+", text, flags=re.MULTILINE))
    section = f"\n## {_chinese_order(section_count + 1)}、{name}\n\n*暂无文章，敬请期待*\n\n---\n"
    marker = "*持续更新，记录成长*"
    if marker in text:
        text = text.replace(marker, section + "\n" + marker, 1)
    else:
        text = text.rstrip() + section + "\n"
    index_path.write_text(text, encoding="utf-8")


def _chinese_order(value: int) -> str:
    numbers = {
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九",
        10: "十",
    }
    return numbers.get(value, str(value))


def find_primary_by_prefix(note_prefix1: str) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in load_category_registry()
            if item.get("note_prefix1") == note_prefix1
        ),
        None,
    )


def find_secondary_by_prefix(note_prefix1: str, note_prefix2: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    primary = find_primary_by_prefix(note_prefix1)
    if not primary:
        return None
    child = next(
        (
            item
            for item in primary.get("children", [])
            if item.get("note_prefix2") == note_prefix2
        ),
        None,
    )
    if not child:
        return None
    return primary, child

