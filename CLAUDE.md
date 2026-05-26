# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hexo 8.1.2 blog ("箓川码笺") using the Butterfly 5.5.5-b1 theme. Chinese-language technical blog deployed to GitHub Pages at https://lucan6290.github.io. Author: lucan.

## Commands

- `npm run server` — local dev server (default http://localhost:4000)
- `npm run build` — generate static files to `public/`
- `npm run clean` — clear cache and `public/`
- `npx hexo new "Post Title"` — create a new post in `source/_posts/`
- `npx hexo new page "Page Name"` — create a new page in `source/<name>/`

## Architecture

- **`_config.yml`** — Hexo site config (URL, categories/tags maps, permalink format `:year/:month/:day/:title/`)
- **`_config.butterfly.yml`** — Butterfly theme config. This is the primary file for all theme customization.
- **`themes/butterfly/`** — Butterfly theme (NOT tracked in git, see `.gitignore`). Download from https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
- **`source/_posts/`** — blog posts organized by category folders (Markdown with YAML front matter)
- **`source/css/custom.css`** — custom CSS styles
- **`scaffolds/`** — post templates for each category

## Deployment

GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on push to `main`: installs deps with `npm ci`, runs `npx hexo generate`, then deploys via GitHub Pages Actions. Manual trigger available via `workflow_dispatch`.

## Conventions

- Categories mapped to English slugs via `category_map` in `_config.yml`
- Posts use YAML front matter with `title`, `date`, `categories`, `tags`, `description`, `cover`
- Post naming: `[category-prefix]-[topic].md` (e.g., `ai-agent-入门笔记.md`)
- Language: `zh-CN`; timezone: `Asia/Shanghai`

## Theme Setup

If `themes/butterfly/` is missing, download it:
```bash
mkdir -p themes
cd themes
# Download from https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
# Extract to themes/butterfly/
```

See `THEME_SETUP.md` for details.