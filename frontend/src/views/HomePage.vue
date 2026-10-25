<template>
  <div class="page">
    <section class="hero" aria-labelledby="home-title">
      <div class="heroText">
        <p class="tagline">箓藏千思，川流不息</p>
        <h1 id="home-title">箓川码笺</h1>
        <p class="lead">在广阔无垠的技术山川中，记录每一次探索、每一个踩坑、每一份感悟，将它们书写成珍贵的技术笺册，沉淀为属于自己的成长宝藏。</p>
        <div class="actions">
          <router-link class="primaryAction" to="/knowledge">进入知识库</router-link>
          <router-link class="secondaryAction" to="/blog">查看博客</router-link>
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
.page {
  --home-top: #e7edf5;
  --home-mid: #fafbfd;
  --home-bottom: #ffffff;
  --home-ink: #111827;
  --home-copy: #374151;
  --home-blue: #2563eb;
  --home-primary: #1f6feb;
  --home-primary-hover: #175dcc;
  --home-primary-ink: #ffffff;
  --home-secondary: #ebedf0;
  --home-secondary-hover: #dfe3e9;
  --home-secondary-ink: #1c1e21;
  background: linear-gradient(180deg, var(--home-top), var(--home-mid) 28%, var(--home-bottom) 72%);
  color: var(--site-text);
}
.hero, .paths { width: min(1160px, calc(100% - 64px)); margin-inline: auto; }
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  align-items: center;
  gap: clamp(42px, 7vw, 100px);
  padding: 78px 0 70px;
}
.sectionLabel {
  margin: 0;
  color: var(--site-accent-ink);
  font-size: .82rem;
  font-weight: 650;
  letter-spacing: .04em;
}
.tagline { margin: 0 0 20px; color: var(--home-blue); font-size: clamp(1rem, 1.55vw, 1.5rem); font-weight: 700; line-height: 1.35; }
.heroText h1 {
  margin: 0;
  color: var(--home-ink);
  font-family: var(--ifm-font-family-base);
  font-size: clamp(4.5rem, 7.1vw, 7.5rem);
  font-weight: 900;
  letter-spacing: -.045em;
  line-height: 1.12;
}
.lead { max-width: 610px; margin: 27px 0 0; color: var(--home-copy); font-size: clamp(1.15rem, 1.55vw, 1.5rem); line-height: 1.72; }
.actions { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; margin-top: 34px; }
.primaryAction, .secondaryAction { display: inline-flex; align-items: center; justify-content: center; min-height: 56px; padding: 0 22px; border-radius: 12px; font-size: 1.18rem; font-weight: 700; text-decoration: none; }
.primaryAction { background: var(--home-primary); color: var(--home-primary-ink); }
.primaryAction:hover { background: var(--home-primary-hover); color: var(--home-primary-ink); }
.secondaryAction { background: var(--home-secondary); color: var(--home-secondary-ink); }
.secondaryAction:hover { background: var(--home-secondary-hover); color: var(--home-secondary-ink); }

:global(html[data-theme='dark'] .page) {
  --home-top: #1b2940;
  --home-mid: #151f31;
  --home-bottom: #121a29;
  --home-ink: #e8effb;
  --home-copy: #cdd9ef;
  --home-blue: #93b8ff;
  --home-primary: #93b8ff;
  --home-primary-hover: #b1ceff;
  --home-primary-ink: #0c1b33;
  --home-secondary: #26354f;
  --home-secondary-hover: #30415d;
  --home-secondary-ink: #e8effb;
}

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
  .tagline { margin-bottom: 15px; font-size: 1.05rem; }
  .heroText h1 { font-size: clamp(3.5rem, 15vw, 5rem); }
  .lead { margin-top: 18px; font-size: 1.05rem; }
  .actions { flex-direction: column; align-items: stretch; gap: 11px; margin-top: 26px; }
  .primaryAction, .secondaryAction { min-height: 50px; font-size: 1.05rem; }
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
