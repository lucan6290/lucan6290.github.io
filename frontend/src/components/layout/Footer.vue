<template>
  <footer class="footer">
    <div class="footer__inner">
      <div class="footer__col">
        <h4>内容</h4>
        <ul>
          <li><router-link to="/knowledge">知识库</router-link></li>
          <li><router-link to="/blog">博客</router-link></li>
          <li><router-link to="/projects">项目</router-link></li>
          <li v-if="hasSeriesRoute(manifest.tree)"><router-link :to="SERIES_ROOT">系列专题</router-link></li>
        </ul>
      </div>
      <div class="footer__col">
        <h4>站点</h4>
        <ul>
          <li><router-link to="/about">关于</router-link></li>
          <li v-if="!manifest.tree.some(node => !node.article && node.name === 'manage-content')"><router-link to="/manage-content">在线管理</router-link></li>
          <li><a href="https://github.com/lucan6290" target="_blank" rel="noopener">GitHub</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__copyright">Copyright © {{ year }} 箓川码笺.</div>
  </footer>
</template>

<script setup lang="ts">
import { useContent } from '@/composables/useContent';
import { hasSeriesRoute, SERIES_ROOT } from '@/utils/seriesPaths';

const { manifest } = useContent();
const year = new Date().getFullYear();
</script>

<style scoped>
.footer {
  border-top: 1px solid var(--site-border);
  background: var(--site-surface);
  padding: 48px 24px 32px;
  margin-top: 64px;
}
.footer__inner {
  max-width: 1160px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 32px;
}
.footer__col h4 {
  margin-bottom: 12px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--site-text);
}
.footer__col ul { list-style: none; }
.footer__col li { margin-bottom: 8px; }
.footer__col a { color: var(--site-text-muted); font-size: 0.88rem; }
.footer__col a:hover { color: var(--ifm-color-primary); }
.footer__copyright {
  max-width: 1160px;
  margin: 32px auto 0;
  color: var(--site-text-muted);
  font-size: 0.82rem;
}
@media (max-width: 700px) {
  .footer__inner { grid-template-columns: 1fr; }
}
</style>
