<template>
  <div class="page">
    <section class="hero" aria-labelledby="home-title">
      <div class="heroText">
        <p class="tagline"><span aria-hidden="true" /> 技术研习 · 工程实践 · 日常记录</p>
        <h1 id="home-title">把技术走过的路，<br />写成可复用的地图。</h1>
        <p class="lead">这里记录长期学习中的知识整理、项目实践与真实复盘。希望每一篇笔记，都能成为下一次出发时找得到的路标。</p>
        <div class="actions">
          <router-link class="primaryAction" to="/knowledge">从知识库开始 <span aria-hidden="true">↗</span></router-link>
          <router-link class="secondaryAction" to="/blog/随笔感想/03-重建个人技术站">先读：重建个人技术站</router-link>
        </div>
      </div>

      <aside class="recent" aria-labelledby="recent-title">
        <div class="recentHeading">
          <div>
            <p class="sectionLabel">持续更新</p>
            <h2 id="recent-title">最近的博客文章</h2>
          </div>
          <router-link to="/blog" aria-label="查看全部博客">全部 <span aria-hidden="true">↗</span></router-link>
        </div>
        <ul v-if="recent.length" class="recentList">
          <li v-for="article in recent" :key="article.path">
            <router-link :to="article.path" class="recentLink">
              <span class="recentCategory">{{ article.frontmatter.tags?.[0] || '博客' }}</span>
              <span class="recentTitle">{{ article.frontmatter.title }}</span>
              <time v-if="article.frontmatter.date" :datetime="article.frontmatter.date">{{ formatDate(article.frontmatter.date) }}</time>
            </router-link>
          </li>
        </ul>
        <p v-else class="recentEmpty">新文章会在这里出现。</p>
      </aside>
    </section>

    <section class="paths" aria-labelledby="paths-title">
      <div class="sectionHeading">
        <div>
          <p class="sectionLabel">按兴趣继续探索</p>
          <h2 id="paths-title">从你关心的方向开始</h2>
        </div>
        <span class="sectionAside">知识整理、过程记录与动手实践</span>
      </div>
      <div class="entryGrid">
        <router-link v-for="entry in entries" :key="entry.href" class="entry" :to="entry.href">
          <span class="entryLine" :class="entry.tone" aria-hidden="true" />
          <div class="entryContent">
            <h3>{{ entry.title }} <span aria-hidden="true">↗</span></h3>
            <p>{{ entry.text }}</p>
          </div>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useContent } from '@/composables/useContent';

const { manifest } = useContent();
const recent = computed(() => Object.values(manifest.value.articles)
  .filter((article) => article.path.startsWith('/blog/'))
  .sort((a, b) => new Date(b.frontmatter.date).getTime() - new Date(a.frontmatter.date).getTime())
  .slice(0, 4));

const entries = [
  { title: '技术知识库', text: '系统整理技术体系、学习笔记与常用参考，方便回看，也方便沿着目录继续深入。', href: '/knowledge', tone: 'accent' },
  { title: '博客随笔', text: '记录项目推进、踩坑复盘和阶段思考，把过程中的经验留存下来。', href: '/blog', tone: 'light' },
  { title: '工程项目', text: '看看想法怎样落到代码里，以及实践过程中的取舍与收获。', href: '/projects', tone: 'lighter' },
];

function formatDate(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai' })
    .format(date)
    .replace(/\//g, '.');
}
</script>

<style scoped>
.page { background: var(--site-background); color: var(--site-text); }
.hero, .paths { width: min(1160px, calc(100% - 64px)); margin-inline: auto; }
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  align-items: center;
  gap: clamp(42px, 7vw, 100px);
  padding: 78px 0 70px;
}
.tagline, .sectionLabel {
  margin: 0;
  color: var(--site-accent-ink);
  font-size: .82rem;
  font-weight: 650;
  letter-spacing: .04em;
}
.tagline { display: flex; align-items: center; gap: 10px; margin-bottom: 21px; }
.tagline > span { width: 7px; height: 7px; border-radius: 50%; background: var(--site-accent); box-shadow: 0 0 0 5px var(--site-accent-soft); }
.heroText h1 {
  margin: 0;
  font-family: var(--site-font-literary);
  font-size: clamp(2.25rem, 4.4vw, 3.7rem);
  font-weight: 600;
  letter-spacing: -.035em;
  line-height: 1.42;
}
.lead { max-width: 570px; margin: 20px 0 0; color: var(--site-text-secondary); font-size: 1rem; line-height: 1.9; }
.actions { display: flex; align-items: center; flex-wrap: wrap; gap: 22px; margin-top: 29px; }
.primaryAction, .secondaryAction { display: inline-flex; align-items: center; gap: 14px; min-height: 44px; font-size: .88rem; font-weight: 650; text-decoration: none; }
.primaryAction { padding: 0 18px; border-radius: 7px; background: var(--site-accent); color: var(--site-on-accent); }
.primaryAction:hover { background: var(--site-accent-hover); color: var(--site-on-accent); }
.secondaryAction { color: var(--site-text-secondary); }
.secondaryAction:hover { color: var(--site-accent-ink); }

.recent { padding: 8px 0 8px 28px; border-left: 1px solid var(--site-border); }
.recentHeading, .sectionHeading { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; }
.recentHeading h2, .sectionHeading h2 { margin: 5px 0 0; font-size: 1.18rem; font-weight: 700; letter-spacing: -.02em; }
.recentHeading > a { flex: none; color: var(--site-text-secondary); font-size: .82rem; }
.recentHeading > a:hover { color: var(--site-accent-ink); }
.recentList { list-style: none; padding: 0; margin: 12px 0 0; }
.recentList li { border-top: 1px solid var(--site-border); }
.recentLink { display: grid; grid-template-columns: minmax(72px, .38fr) minmax(0, 1fr) auto; align-items: baseline; gap: 12px; padding: 13px 0; color: var(--site-text); text-decoration: none; }
.recentCategory { overflow: hidden; color: var(--site-accent-ink); font-size: .82rem; text-overflow: ellipsis; white-space: nowrap; }
.recentTitle { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 2; font-size: .9rem; font-weight: 550; line-height: 1.45; }
.recentLink:hover .recentTitle { color: var(--site-accent-ink); }
.recentLink time { color: var(--site-text-secondary); font-size: .82rem; white-space: nowrap; }
.recentEmpty { margin-top: 20px; color: var(--site-text-muted); font-size: .86rem; }

.paths { padding: 30px 0 74px; border-top: 1px solid var(--site-border); }
.sectionAside { color: var(--site-text-muted); font-size: .76rem; }
.entryGrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 30px; margin-top: 25px; }
.entry { display: flex; gap: 17px; min-height: 122px; padding: 20px 0; color: var(--site-text); text-decoration: none; }
.entryLine { flex: none; width: 3px; height: 38px; margin-top: 4px; border-radius: 3px; background: var(--site-accent); }
.entryLine.light { background: var(--ifm-color-primary-light); }
.entryLine.lighter { background: var(--ifm-color-primary-lighter); }
.entryContent { min-width: 0; }
.entry h3 { display: flex; justify-content: space-between; gap: 12px; margin: 0; font-size: 1rem; font-weight: 700; }
.entry h3 span { color: var(--site-text-muted); font-size: .9rem; font-weight: 400; }
.entry p { margin: 8px 0 0; color: var(--site-text-muted); font-size: .8rem; line-height: 1.75; }
.entry:hover h3, .entry:hover h3 span { color: var(--site-accent-ink); }

@media (max-width: 900px) {
  .hero { grid-template-columns: minmax(0, 1fr); gap: 42px; padding-top: 60px; }
  .recent { max-width: 700px; }
}
@media (max-width: 700px) {
  .hero, .paths { width: calc(100% - 40px); }
  .hero { gap: 34px; padding: 43px 0 48px; }
  .heroText h1 { font-size: clamp(2rem, 8vw, 3rem); line-height: 1.4; }
  .lead { margin-top: 16px; font-size: .92rem; }
  .actions { gap: 16px; margin-top: 23px; }
  .recent { padding-left: 17px; }
  .recentLink { grid-template-columns: minmax(62px, .34fr) minmax(0, 1fr); gap: 7px 10px; }
  .recentLink time { grid-column: 2; }
  .paths { padding: 26px 0 45px; }
  .sectionHeading { align-items: flex-start; }
  .sectionHeading h2 { font-size: 1.05rem; }
  .sectionAside { display: none; }
  .entryGrid { grid-template-columns: 1fr; gap: 0; margin-top: 15px; }
  .entry { min-height: 0; padding: 17px 0; border-top: 1px solid var(--site-border); }
}
@media (prefers-reduced-motion: reduce) {
  .primaryAction { transition: none; }
}
</style>
