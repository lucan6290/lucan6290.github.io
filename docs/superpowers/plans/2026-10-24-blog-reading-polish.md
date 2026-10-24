# Blog Reading Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the public Vue blog's reading and navigation experience while keeping its current green and handwritten visual identity.

**Architecture:** Reuse the existing Vue components and CSS tokens. Adjust the reading styles in MarkdownRenderer and ArticleView; give the shared sidebar a compact mobile disclosure; make FloatToc reachable through a visible button; refine HomePage, ArticleList and Navbar without changing the content pipeline.

**Tech Stack:** Vue 3.5, Vite 6, TypeScript, scoped CSS, ByteMD, pnpm.

**Spec:** `docs/博客视觉与阅读体验完善方案.md`

## Global Constraints

- Preserve existing theme, routes, content, and existing uncommitted edits.
- No new dependency, API, content migration or automatic Git commit.
- Keep the fixed dev port at 3400 and do not run old and new frontends together.
- Do not edit `frontend/src/generated/` by hand.
- Verify desktop, tablet and mobile; light and dark; keyboard and pointer use.

## Review Focus

- Desktop collapse preference must not force the mobile directory open on first visit.
- Route changes must not leave a prior article's table of contents visible.
- Long Chinese titles, long code and wide tables must stay readable without whole-page overflow.
- Closing an open table of contents with Escape must restore focus to its trigger.
- Knowledge pages sharing the sidebar and article renderer must keep their existing navigation behavior.

---

### Task 1: Reading layout and type

**Files:** `frontend/src/components/article/MarkdownRenderer.vue`, `frontend/src/views/ArticleView.vue`.

- [x] Capture and inspect a long article at desktop and phone widths; confirm the existing font sizes and layout.
- [x] Set body text to about 17px desktop and 16px mobile, line-height about 1.8–1.85 and reading measure about 820px; tune code, table, quote and image spacing without changing Markdown data.
- [x] Recheck long Chinese headings and long code/table overflow in the browser.

### Task 2: Compact mobile directory

**Files:** `frontend/src/components/sidebar/ResizableSidebar.vue`.

- [x] Verify current phone view puts the expanded directory before article title.
- [x] Add an independent mobile disclosure state, initially closed and reset on route change, with a 44px target and accurate `aria-expanded`/`aria-controls`; preserve desktop collapse and resize state.
- [x] Check mobile initial view, expand/collapse, route change and desktop resize preference.

### Task 3: Explicit article table of contents

**Files:** `frontend/src/components/toc/FloatToc.vue`, and `frontend/src/views/ArticleView.vue` only if needed for placement.

- [x] Verify current hover-only desktop access and hidden mobile access.
- [x] Add a visible “本文目录” trigger and nonmodal panel, limit dimensions, add Escape/outside-click closing, restore focus, and refresh headings on route changes. Hide trigger when headings are absent.
- [x] Check pointer, keyboard, mobile chapter navigation, route switching and reduced motion.

### Task 4: List and navigation polish

**Files:** `frontend/src/views/HomePage.vue`, `frontend/src/components/list/ArticleList.vue`, `frontend/src/components/layout/Navbar.vue`, `frontend/src/views/ArticleView.vue` if tag styles need alignment.

- [x] Verify long recent title truncation and current navigation state.
- [x] Allow recent titles to use two lines; increase date legibility; align article list and tags; indicate active top-level section and enlarge touch targets.
- [x] Check Home, blog, knowledge, article and theme/menu interactions at mobile and desktop widths.

### Task 5: Integration and review

**Files:** this plan status only if progress notation is useful; no new product file by default.

- [x] Run `pnpm test` and `pnpm build` from `frontend/` and inspect full output.
- [x] Use the design skill's inspector and browser screenshots at 390, 768 and 1440 widths, interpreting its aesthetic warnings against the user's existing theme preference.
- [x] Compare current pages with the baseline, review the final diff for unrelated edits, and report residual limitations.

No commit step is included because the repository's `AGENTS.md` forbids an AI commit without a separate explicit commit instruction.
