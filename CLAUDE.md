# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hexo 8.x blog ("箓川码笺") using the Butterfly 5.5.5-b1 theme. Chinese-language technical blog deployed to GitHub Pages at https://lucan6290.github.io. Author: lucan.

## Commands

- `npm run server` — local dev server (default http://localhost:4000)
- `npm run build` — generate static files to `public/`
- `npm run clean` — clear cache and `public/`
- `npm run deploy` — deploy via hexo-deployer-git
- `npx hexo new "Post Title"` — create a new post in `source/_posts/`
- `npx hexo new page "Page Name"` — create a new page in `source/<name>/`

## Architecture

- **`_config.yml`** — Hexo site config (URL, categories/tags maps, permalink format `:year/:month/:day/:title/`)
- **`_config.butterfly.yml`** — Butterfly theme config (overlays `themes/butterfly/_config.yml`). This is the primary file for all theme customization.
- **`themes/butterfly/`** — Butterfly theme committed as project files (not a submodule). Avoid editing files here unless modifying the theme itself; use `_config.butterfly.yml` for configuration.
- **`source/_posts/`** — blog posts (Markdown with YAML front matter, `post_asset_folder: true` means each post can have a same-named folder for assets)
- **`source/`** — other pages (`about/`, `categories/`, `tags/`)
- **`scaffolds/`** — post/page/draft templates

## Deployment

GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on push to `main`: installs deps with `npm ci`, runs `npx hexo generate`, then deploys `public/` via the official GitHub Pages Actions. Dependabot checks npm dependencies daily.

## Conventions

- Categories are mapped to English slugs via `category_map` in `_config.yml` (e.g., "技术研习" → "tech-study"). Default category: "技术研习".
- Posts use YAML front matter with `title`, `date`, `categories`, `tags`, `description`, and optional `cover`.
- Post assets (images etc.) go in a folder matching the post filename under `source/_posts/`.
- Language is `zh-CN`; timezone `Asia/Shanghai`.
