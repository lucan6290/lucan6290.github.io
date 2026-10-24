<template>
  <aside
    class="sidebar-container"
    :class="{ 'sidebar-container--collapsed': collapsed, 'sidebar-container--resizing': resizing }"
    :style="{ '--sidebar-width': collapsed ? '0px' : `${width}px` }"
    aria-label="目录侧栏"
  >
    <button
      class="sidebar-mobile-toggle"
      type="button"
      aria-label="栏目目录"
      aria-controls="sidebar-mobile-content"
      :aria-expanded="mobileOpen"
      @click="mobileOpen = !mobileOpen"
    >
      栏目目录 <span aria-hidden="true">{{ mobileOpen ? '⌃' : '⌄' }}</span>
    </button>
    <button
      v-if="collapsed"
      class="sidebar-expand"
      type="button"
      aria-label="展开目录"
      title="展开目录"
      @click="toggleCollapsed"
    >
      <span aria-hidden="true">›</span>
      <span>展开目录</span>
    </button>

    <div
      id="sidebar-mobile-content"
      class="sidebar-panel"
      :class="{ 'sidebar-panel--collapsed': collapsed, 'sidebar-panel--mobile-open': mobileOpen }"
    >
      <div class="sidebar-toolbar">
        <button
          class="sidebar-toggle"
          type="button"
          aria-label="收起侧栏"
          title="收起侧栏"
          @click="toggleCollapsed"
        >
          <span aria-hidden="true">‹</span>
        </button>
      </div>
      <slot />
      <div
        class="sidebar-resizer"
        role="separator"
        aria-label="调整目录宽度"
        aria-orientation="vertical"
        aria-valuemin="240"
        aria-valuemax="420"
        :aria-valuenow="width"
        tabindex="0"
        @pointerdown="startResize"
        @pointermove="moveResize"
        @pointerup="finishResize"
        @pointercancel="finishResize"
        @keydown="resizeByKeyboard"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';

const STORAGE_KEY = 'xiaocancoding.sidebar-layout';
const MIN_WIDTH = 240;
const MAX_WIDTH = 420;

function clampWidth(value: number) {
  return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, Math.round(value)));
}

function defaultWidth() {
  return Math.min(340, Math.max(280, Math.round(window.innerWidth * 0.22)));
}

function loadLayout() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null') as { width?: number; collapsed?: boolean } | null;
    return {
      width: typeof saved?.width === 'number' ? clampWidth(saved.width) : defaultWidth(),
      collapsed: saved?.collapsed === true,
    };
  } catch {
    return { width: defaultWidth(), collapsed: false };
  }
}

const initialLayout = loadLayout();
const width = ref(initialLayout.width);
const collapsed = ref(initialLayout.collapsed);
const mobileOpen = ref(false);
const resizing = ref(false);
const route = useRoute();
watch(() => route.fullPath, () => { mobileOpen.value = false; });
let startX = 0;
let startWidth = width.value;

function saveLayout() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ width: width.value, collapsed: collapsed.value }));
  } catch {
    // The sidebar remains usable when browser storage is unavailable.
  }
}

function toggleCollapsed() {
  collapsed.value = !collapsed.value;
  saveLayout();
}

function startResize(event: PointerEvent) {
  if (event.button !== 0) return;
  event.preventDefault();
  startX = event.clientX;
  startWidth = width.value;
  resizing.value = true;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function moveResize(event: PointerEvent) {
  if (!resizing.value) return;
  width.value = clampWidth(startWidth + event.clientX - startX);
}

function finishResize(event: PointerEvent) {
  if (!resizing.value) return;
  resizing.value = false;
  const handle = event.currentTarget as HTMLElement;
  if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
  saveLayout();
}

function resizeByKeyboard(event: KeyboardEvent) {
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
  event.preventDefault();
  width.value = clampWidth(width.value + (event.key === 'ArrowRight' ? 16 : -16));
  saveLayout();
}
</script>

<style scoped>
.sidebar-container {
  position: sticky;
  top: var(--ifm-navbar-height);
  box-sizing: border-box;
  width: var(--sidebar-width);
  height: calc(100vh - var(--ifm-navbar-height));
  overflow-x: hidden;
  overflow-y: auto;
  border-right: 1px solid var(--site-border);
  background: var(--site-background);
  padding: 16px 18px 96px 14px;
  transition: width 180ms ease, padding 180ms ease;
}
.sidebar-container--collapsed {
  height: 0;
  min-height: 0;
  overflow: visible;
  border: 0;
  padding: 0;
  background: transparent;
  transition: none;
}
.sidebar-container--resizing { transition: none; }
.sidebar-panel--collapsed { display: none; }
.sidebar-toolbar { display: flex; justify-content: flex-end; margin: -5px -7px 10px; }
.sidebar-mobile-toggle { display: none; }
.sidebar-toggle,
.sidebar-expand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 32px;
  padding: 4px 9px;
  border-radius: 7px;
  background: var(--site-accent-soft);
  color: var(--site-text-secondary);
  font-size: .82rem;
}
.sidebar-toggle { width: 32px; padding: 0; font-size: 1.3rem; }
.sidebar-toggle:hover,
.sidebar-expand:hover { background: var(--site-border); color: var(--ifm-color-primary); }
.sidebar-expand { position: fixed; top: calc(var(--ifm-navbar-height) + 14px); left: 8px; z-index: 1002; box-shadow: 0 4px 14px var(--site-shadow); }
.sidebar-expand > span:first-child { font-size: 1.2rem; line-height: 1; }
.sidebar-resizer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 7px;
  cursor: col-resize;
  touch-action: none;
  background: transparent;
}
.sidebar-resizer:hover,
.sidebar-container--resizing .sidebar-resizer { background: var(--site-accent-soft); }
.sidebar-resizer:focus-visible { outline-offset: -3px; }

@media (max-width: 996px) {
  .sidebar-container,
  .sidebar-container--collapsed {
    position: static;
    width: 100%;
    height: auto;
    overflow: visible;
    border-right: 0;
    padding: 0;
    transition: none;
  }
  .sidebar-mobile-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    min-height: 44px;
    padding: 0 20px;
    border-bottom: 1px solid var(--site-border);
    color: var(--site-text-secondary);
    font-size: .88rem;
    font-weight: 600;
  }
  .sidebar-mobile-toggle:hover { color: var(--site-accent-ink); background: var(--site-accent-soft); }
  .sidebar-panel { display: none; }
  .sidebar-panel--mobile-open {
    display: block;
    padding: 12px 20px 20px;
    border-bottom: 1px solid var(--site-border);
  }
  .sidebar-toolbar, .sidebar-expand { display: none; }
  .sidebar-resizer { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar-container { transition: none; }
}
</style>
