<template>
  <div class="toc-hover-zone" @mouseenter="show" @mouseleave="scheduleHide" />
  <aside
    class="custom-toc-float"
    :class="{ 'custom-toc-float--visible': visible }"
    @mouseenter="cancelHide"
    @mouseleave="scheduleHide"
  >
    <div class="toc-header">
      <span class="toc-header__title">目录</span>
      <button class="toc-header__btn toc-header__btn--hide" type="button" title="隐藏大纲" @click="hide">✕</button>
    </div>
    <ul v-if="headings.length" class="table-of-contents">
      <li v-for="h in headings" :key="h.id" class="toc-tree-item" :class="`toc-tree-item--level-${h.level}`">
        <a
          class="table-of-contents__link"
          :class="{ 'table-of-contents__link--active': activeId === h.id }"
          :href="`#${h.id}`"
          @click.prevent="scrollTo(h.id)"
        >{{ h.text }}</a>
      </li>
    </ul>
    <p v-else class="toc-empty">本页无标题</p>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';

type Heading = { id: string; text: string; level: number };

const visible = ref(false);
const activeId = ref('');
const headings = ref<Heading[]>([]);
let hideTimer: number | null = null;
let observer: IntersectionObserver | null = null;

function show() { cancelHide(); visible.value = true; document.body.classList.add('toc-panel-visible'); }
function hide() { cancelHide(); visible.value = false; document.body.classList.remove('toc-panel-visible'); }
function scheduleHide() { hideTimer = window.setTimeout(hide, 280); }
function cancelHide() { if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; } }

function collectHeadings() {
  const nodes = document.querySelectorAll('.md-viewer h2, .md-viewer h3');
  const list: Heading[] = [];
  nodes.forEach((n) => {
    const el = n as HTMLElement;
    if (!el.id) el.id = encodeURIComponent(el.textContent?.trim() || '').replace(/%/g, '-').slice(0, 80);
    list.push({ id: el.id, text: el.textContent?.trim() || '', level: el.tagName === 'H2' ? 0 : 1 });
  });
  headings.value = list;
}

function scrollTo(id: string) {
  const el = document.getElementById(id);
  if (el) {
    const y = el.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: y, behavior: 'smooth' });
    activeId.value = id;
  }
}

function setupObserver() {
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) { activeId.value = e.target.id; break; }
      }
    },
    { rootMargin: '-80px 0px -70% 0px', threshold: 0 },
  );
  headings.value.forEach((h) => {
    const el = document.getElementById(h.id);
    if (el) observer!.observe(el);
  });
}

onMounted(() => {
  // 延迟收集，等 MD 渲染完成
  setTimeout(() => { collectHeadings(); setupObserver(); }, 300);
});
onUnmounted(() => {
  observer?.disconnect();
  cancelHide();
  document.body.classList.remove('toc-panel-visible');
});
</script>

<style scoped>
.toc-hover-zone {
  position: fixed; top: 0; right: 0; bottom: 0; width: 40px; z-index: 198;
}
.custom-toc-float {
  position: fixed; top: 0; right: 0; bottom: 0; width: 280px;
  padding: 12px 16px 24px;
  background: var(--site-background);
  border-left: 1px solid var(--site-border);
  z-index: 201;
  overflow-y: auto;
  transform: translateX(100%); opacity: 0; visibility: hidden; pointer-events: none;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease, visibility 0s linear 0.25s;
}
.custom-toc-float--visible {
  transform: translateX(0); opacity: 1; visibility: visible; pointer-events: auto;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease, visibility 0s linear 0s;
}
.toc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; position: sticky; top: 0; background: var(--site-background); z-index: 2; padding: 4px 0 8px; }
.toc-header__title { font-size: 20px; font-weight: 700; color: var(--site-text); }
.toc-header__btn { width: 32px; height: 32px; border-radius: 10px; background: var(--site-accent-soft); color: var(--site-text-muted); display: grid; place-items: center; transition: background 180ms, color 180ms; }
.toc-header__btn:hover { background: var(--site-border); color: var(--ifm-color-primary); }

.table-of-contents { list-style: none; padding: 0; margin: 0; position: relative; }
.table-of-contents::after { content: ''; position: absolute; top: 2px; bottom: 2px; left: 5px; width: 2px; border-radius: 1px; background: var(--site-border); }
.toc-tree-item { padding: 2px 0; }
.table-of-contents__link {
  display: block; padding: 3px 0 3px 18px; color: var(--site-text-secondary); font-size: 15px; line-height: 1.7; word-break: break-word; text-decoration: none; transition: color 150ms;
}
.toc-tree-item--level-1 .table-of-contents__link { font-size: 14px; color: var(--site-text-muted); padding-left: 32px; }
.table-of-contents__link:hover { color: var(--ifm-color-primary); }
.table-of-contents__link--active { color: var(--ifm-color-primary) !important; font-weight: 600; }
.toc-empty { color: var(--site-text-muted); font-size: 14px; padding: 12px 0; }

@media (max-width: 996px) {
  .toc-hover-zone, .custom-toc-float { display: none; }
}
</style>
