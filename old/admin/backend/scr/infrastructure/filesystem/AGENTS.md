# infrastructure/filesystem — AGENTS.md

> 文件与 Markdown 基础能力。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 14 节。

## 职责

文件系统读写与 Markdown 解析的底层能力，向上层屏蔽文件细节。

## 内容

- `filesystem_service.py`：文件读写/路径安全。
- `markdown_service.py`：Front Matter 拆分与解析（`MarkdownService` / `ParsedMarkdown`）。

## 约定

- 文件系统访问集中在 `site/docs`、`site/blog` 白名单目录，禁止路径穿越。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
