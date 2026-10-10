<template>
  <main class="page-shell">
    <section class="simple-page">
      <p class="eyebrow">Projects</p>
      <h1>项目展示</h1>
      <div class="project-list">
        <article v-for="p in projects" :key="p.name" class="project-item">
          <h2>{{ p.name }}</h2>
          <p>{{ p.description }}</p>
        </article>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
const projects = [
  { name: '个人技术站', description: '基于自研前端 + Vite + Vue3 的长期知识库、博客与项目展示站。' },
  { name: '内容管理端', description: '面向 Markdown 写作的本地 Admin，用于创建、编辑和管理站点内容。' },
];
</script>

<style scoped>
.page-shell {
  min-height: calc(100vh - var(--ifm-navbar-height));
  background: linear-gradient(180deg, #f8fafc, #fff 36%);
  padding: 64px 24px 96px;
}
html[data-theme='dark'] .page-shell { background: var(--site-background); }
.simple-page { width: min(880px, 100%); margin: 0 auto; }
.eyebrow { margin: 0 0 12px; color: var(--ifm-color-primary); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.simple-page h1 { margin: 0 0 22px; color: var(--site-text); font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.12; }
.project-list { display: grid; gap: 18px; margin-top: 32px; }
.project-item { border: 1px solid var(--site-border); border-radius: 8px; background: var(--site-surface); padding: 24px; }
.project-item h2 { margin: 0 0 8px; color: var(--site-text); }
.project-item p { margin: 0; color: var(--site-text-secondary); line-height: 1.75; }
</style>
