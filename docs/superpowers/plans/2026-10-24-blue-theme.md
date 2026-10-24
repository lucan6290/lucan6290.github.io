# Blue Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the public site's light and dark themes with the existing blue Logo.

**Architecture:** Keep the current Vue pages and styles. Change shared CSS tokens so interactive components inherit the blue palette, then update only the three decorative entry lines on the homepage.

**Tech Stack:** Vue 3.5, Vite 6, CSS custom properties, pnpm.

**Spec:** `docs/博客蓝色主题调整方案.md`

## Global Constraints

- Preserve existing layout, typography, content and the user-owned Logo.
- Preserve other uncommitted changes. Do not commit or add dependencies.
- Keep fixed development port 3400. Do not edit generated content.

## Review Focus

- White text on the light primary button and dark text on the dark primary button must remain legible.
- Hover and active navigation states must keep visible contrast in both themes.
- Warning, danger, code syntax and keyboard focus retain their semantic distinctions.
- No former teal primary interaction or teal decorative homepage line remains.
- Knowledge and article components consuming shared tokens remain readable.

---

### Task 1: Shared color tokens

**Files:** `frontend/src/styles/tokens.css`.

- [x] Replace primary, accent, surface, text and border values for both themes using the approved palette.
- [x] Verify representative color pairs meet contrast targets; preserve warning/danger semantics.

### Task 2: Homepage decorative accents

**Files:** `frontend/src/views/HomePage.vue`.

- [x] Change the three section entry lines to related blue shades without changing their content or layout.
- [x] Check that light and dark homepage controls and labels still have a clear hierarchy.

### Task 3: Visual and code verification

**Files:** No additional product file unless a fixed-color remnant is found.

- [x] Inspect light home/article at 390, 768 and 1440px; spot-check dark home/list/article/knowledge across desktop, tablet and mobile, including controls and dark code.
- [x] Run `pnpm test`, `pnpm build`, and `git diff --check`; review only this change's diff before reporting.

No commit step is included because the repository's `AGENTS.md` requires a separate explicit commit instruction.
