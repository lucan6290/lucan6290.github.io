<template>
  <div class="page">
    <section class="hero" aria-labelledby="home-title">
      <div class="heroText">
        <p class="kicker"><span /> 一座持续生长的数字花园</p>
        <h1 id="home-title">把探索写成笔记，<br /><span>让知识慢慢生长。</span></h1>
        <p class="lead">你好，欢迎来到箓川码笺。<br />在这里，记录技术的脉络、实践的足迹，<br class="desktopBreak" />以及那些值得留下的思考。</p>
        <div class="actions">
          <router-link class="primaryAction" to="/blog">开始阅读 <span aria-hidden="true">↗</span></router-link>
          <router-link class="secondaryAction" to="/knowledge">探索知识库 <span aria-hidden="true">→</span></router-link>
        </div>
        <div class="heroFootnote"><span aria-hidden="true">✳</span> 保持好奇，认真记录，缓慢而坚定地向前。</div>
      </div>
      <div class="garden">
        <div class="gardenOrbit" aria-hidden="true" />
        <span class="gardenLabel" aria-hidden="true">IDEAS TAKE ROOT HERE</span>
        <div class="notebook">
          <div class="notebookTop"><span>箓川 · 手记</span><span aria-hidden="true">VOL. 01</span></div>
          <div class="notebookTitle">于技术之川，<br />拾字成箓。</div>
          <p class="notebookSubtitle">从一个问题出发，走向更大的世界。</p>
          <div class="notebookLinks">
            <router-link to="/knowledge/tech-study"><span>01</span> 技术研习 <span aria-hidden="true">↗</span></router-link>
            <router-link to="/knowledge/project-practice"><span>02</span> 项目实战 <span aria-hidden="true">↗</span></router-link>
            <router-link to="/knowledge/resource-sharing"><span>03</span> 资源分享 <span aria-hidden="true">↗</span></router-link>
          </div>
          <div class="notebookBottom"><span><i /> 学习不止，更新不停</span><span aria-hidden="true">✳</span></div>
        </div>
        <span class="gardenNote" aria-hidden="true">一点积累，一点生长。</span>
      </div>
    </section>

    <section class="paths" aria-labelledby="paths-title">
      <div class="sectionHeading">
        <div><p class="eyebrow">EXPLORE THE GARDEN</p><h2 id="paths-title">找到你感兴趣的那一页</h2></div>
        <span class="sectionAside">不同的入口，同样的好奇心</span>
      </div>
      <div class="entryGrid">
        <router-link v-for="e in entries" :key="e.href" class="entry" :to="e.href">
          <div class="entryTop"><span class="entryIcon" :class="e.tone"><EntryIcon :name="e.icon" /></span><span class="entryNumber">{{ e.number }}</span></div>
          <h3>{{ e.title }}<span aria-hidden="true">↗</span></h3>
          <strong>{{ e.label }}</strong>
          <p>{{ e.text }}</p>
        </router-link>
      </div>
    </section>

    <section v-if="recent.length" class="notes" aria-labelledby="notes-title">
      <div class="sectionHeading">
        <div><p class="eyebrow">RECENT NOTES</p><h2 id="notes-title">最近写下的思考</h2></div>
        <router-link class="textLink" to="/blog">全部文章 <span aria-hidden="true">→</span></router-link>
      </div>
      <div class="postGrid">
        <article v-for="art in recent" :key="art.path" class="post">
          <router-link :to="art.path" class="postLink">
            <div class="postTop"><span class="category">{{ art.frontmatter.tags?.[0] || '随手记录' }}</span><span class="postArrow" aria-hidden="true">↗</span></div>
            <h3>{{ art.frontmatter.title }}</h3>
            <p v-if="art.excerpt" class="description">{{ art.excerpt }}</p>
            <div class="postMeta">
              <time v-if="art.frontmatter.date" :datetime="art.frontmatter.date">{{ formatDate(art.frontmatter.date) }}</time>
            </div>
          </router-link>
        </article>
      </div>
    </section>

    <section class="closing" aria-label="关于作者">
      <span class="closingMark" aria-hidden="true">✳</span>
      <div><h2>不止于记录，更期待与你共鸣。</h2><p>如果某一页恰好对你有用，这座小小的数字花园就有了意义。</p></div>
      <router-link to="/about">认识一下我 <span aria-hidden="true">↗</span></router-link>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { useContent } from '@/composables/useContent';

const { getRecent } = useContent();
const recent = computed(() => getRecent(3));

const entries = [
  { number: '01', title: '知识库', label: '把零散知识，连成体系', text: '技术笔记、系统梳理与常用参考，写给每一个想弄明白的自己。', href: '/knowledge', icon: 'book', tone: 'tone-accent' },
  { number: '02', title: '博客随笔', label: '记录当下，也回望来路', text: '关于 AI、开发和成长的真实观察。分享结论，也分享思考的过程。', href: '/blog', icon: 'pen', tone: 'tone-warm' },
  { number: '03', title: '项目实践', label: '让想法，在代码里落地', text: '从一个念头到可以运行的作品，留下实践、取舍和踩坑的经验。', href: '/projects', icon: 'code', tone: 'tone-cool' },
];

function EntryIcon({ name }: { name: string }) {
  const paths: Record<string, any[]> = {
    book: [h('path', { d: 'M12 5v15M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3Z' })],
    pen: [h('path', { d: 'm15 4 5 5M5 15 16 4a2.1 2.1 0 0 1 3 3L8 18l-5 2Z' }), h('path', { d: 'M13 20h8' })],
    code: [h('path', { d: 'm8 6-6 6 6 6m8-12 6 6-6 6m-3-14-2 16' })],
  };
  return h('svg', { viewBox: '0 0 24 24', width: 22, height: 22, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': true }, paths[name] || []);
}

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai' }).format(d).replace(/\//g, '.');
}
</script>

<style scoped>
.page { background: var(--site-background); color: var(--site-text); }
.hero, .paths, .notes, .closing { width: min(1160px, calc(100% - 64px)); margin-inline: auto; }
.hero { display: grid; grid-template-columns: 1.2fr 0.8fr; align-items: center; gap: 48px; padding: 86px 0 82px; }
.kicker { display: flex; align-items: center; gap: 10px; margin: 0 0 24px; color: var(--site-accent); font-size: .83rem; font-weight: 600; letter-spacing: .1em; }
.kicker > span { width: 7px; height: 7px; border-radius: 50%; background: var(--site-accent); box-shadow: 0 0 0 5px var(--site-accent-soft); }
.heroText h1 { margin: 0; font-size: clamp(2.2rem, 3.6vw, 3.45rem); font-weight: 650; letter-spacing: -.04em; line-height: 1.4; }
.heroText h1 > span { color: var(--site-accent); }
.lead { margin: 25px 0 0; color: var(--site-text-secondary); font-size: 1rem; line-height: 1.95; }
.actions { display: flex; flex-wrap: wrap; align-items: center; gap: 26px; margin-top: 30px; }
.primaryAction, .secondaryAction { display: inline-flex; align-items: center; justify-content: center; gap: 28px; min-height: 48px; font-size: .9rem; font-weight: 600; transition: background 180ms, transform 180ms; text-decoration: none; }
.primaryAction { border: 1px solid var(--site-accent); border-radius: 7px; padding: 10px 22px; background: var(--site-accent); color: var(--site-on-accent); }
.primaryAction:hover { color: var(--site-on-accent); background: var(--ifm-color-primary-dark); transform: translateY(-2px); }
.secondaryAction { color: var(--site-text); }
.secondaryAction:hover { color: var(--site-accent); }
.heroFootnote { display: flex; gap: 9px; align-items: center; margin-top: 31px; color: var(--site-text-muted); font-size: .76rem; }
.heroFootnote > span { color: var(--site-warm); font-size: 1.2rem; }

.garden { position: relative; padding: 18px 16px 25px 12px; isolation: isolate; }
.gardenOrbit { position: absolute; inset: -8px -32px 0; z-index: -2; border: 1px solid var(--site-border); border-radius: 50%; transform: rotate(-24deg); }
.gardenOrbit::before { position: absolute; inset: 22px; border: 1px dashed var(--site-border); border-radius: 50%; content: ''; }
.gardenOrbit::after { position: absolute; top: 56px; right: 48px; width: 13px; height: 13px; border-radius: 50%; background: var(--site-warm); content: ''; }
.gardenLabel { position: absolute; top: -10px; left: 4px; color: var(--site-text-muted); font-family: var(--ifm-font-family-monospace); font-size: .57rem; letter-spacing: .16em; transform: rotate(-8deg); }
.notebook { position: relative; padding: 28px 30px 20px; border: 1px solid var(--site-border); border-radius: 5px 13px 13px 5px; background: var(--site-surface); box-shadow: 9px 10px 0 -1px var(--site-background), 9px 10px 0 0 var(--site-border), 0 24px 45px -22px var(--site-shadow); transform: rotate(-4deg); }
.notebook::before { position: absolute; top: 0; bottom: 0; left: 9px; border-left: 1px solid var(--site-border); content: ''; }
.notebookTop { display: flex; align-items: center; justify-content: space-between; padding-bottom: 17px; border-bottom: 1px solid var(--site-border); color: var(--site-text-muted); font-size: .68rem; letter-spacing: .1em; }
.notebookTop span:last-child { font-family: var(--ifm-font-family-monospace); font-size: .57rem; }
.notebookTitle { margin-top: 20px; color: var(--site-accent); font-family: var(--site-font-literary); font-size: 2.35rem; font-weight: 600; line-height: 1.45; letter-spacing: .1em; }
.notebookSubtitle { margin: 12px 0 17px; color: var(--site-text-muted); font-size: .68rem; }
.notebookLinks { border-top: 1px solid var(--site-border); }
.notebookLinks a { display: flex; gap: 15px; align-items: center; min-height: 44px; border-bottom: 1px solid var(--site-border); color: var(--site-text); font-size: .76rem; text-decoration: none; }
.notebookLinks a > span:first-child { color: var(--site-text-muted); font-family: var(--ifm-font-family-monospace); font-size: .59rem; }
.notebookLinks a > span:last-child { margin-left: auto; color: var(--site-accent); }
.notebookLinks a:hover { color: var(--site-accent); }
.notebookBottom { display: flex; align-items: center; justify-content: space-between; margin-top: 18px; font-size: .6rem; color: var(--site-text-muted); }
.notebookBottom > span:first-child { display: flex; align-items: center; gap: 7px; }
.notebookBottom > span:last-child { color: var(--site-accent); font-size: 1.6rem; line-height: 1; }
.notebookBottom i { width: 5px; height: 5px; border-radius: 50%; background: var(--site-accent); display: inline-block; }
.gardenNote { position: absolute; bottom: -11px; right: 5px; color: var(--site-text-muted); font-size: .74rem; font-family: var(--site-font-literary); transform: rotate(-4deg); }

.paths { padding: 42px 0 50px; border-top: 1px solid var(--site-border); }
.sectionHeading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.eyebrow { margin: 0 0 8px; font-family: var(--ifm-font-family-monospace); font-size: .6rem; font-weight: 500; letter-spacing: .17em; color: var(--site-text-muted); }
.sectionHeading h2 { margin: 0; font-size: 1.4rem; font-weight: 650; letter-spacing: -.03em; }
.sectionAside { padding-bottom: 2px; color: var(--site-text-muted); font-size: .76rem; }
.entryGrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.entry { padding: 25px 26px; border: 1px solid var(--site-border); border-radius: 10px; background: var(--site-surface); color: var(--site-text); transition: border-color 180ms, transform 180ms, box-shadow 180ms; text-decoration: none; }
.entry:hover { color: var(--site-text); border-color: var(--site-accent); transform: translateY(-3px); box-shadow: 0 12px 30px -24px var(--site-shadow); }
.entryTop { display: flex; align-items: center; justify-content: space-between; margin-bottom: 23px; }
.entryIcon { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 10px; }
.entryIcon.tone-accent { background: var(--site-accent-soft); color: var(--site-accent); }
.entryIcon.tone-warm { background: var(--site-warm-soft); color: var(--site-warm); }
.entryIcon.tone-cool { background: var(--site-cool-soft); color: var(--site-cool); }
.entryNumber { color: var(--site-text-muted); font-family: var(--ifm-font-family-monospace); font-size: .65rem; }
.entry h3 { display: flex; justify-content: space-between; margin: 0 0 12px; font-size: 1.13rem; font-weight: 650; }
.entry h3 > span { color: var(--site-text-muted); font-size: 1rem; transition: color 180ms; }
.entry:hover h3 > span { color: var(--site-accent); }
.entry strong { color: var(--site-text-secondary); font-size: .79rem; font-weight: 500; }
.entry p { margin: 8px 0 0; color: var(--site-text-muted); font-size: .78rem; line-height: 1.85; }

.notes { padding: 12px 0 50px; }
.textLink { display: inline-flex; gap: 15px; align-items: center; min-height: 38px; color: var(--site-accent); font-size: .8rem; font-weight: 500; white-space: nowrap; text-decoration: none; }
.postGrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.post { border: 1px solid var(--site-border); border-radius: 10px; background: var(--site-surface); overflow: hidden; transition: border-color 180ms, transform 180ms; }
.post:hover { border-color: var(--site-accent); transform: translateY(-2px); }
.postLink { display: flex; flex-direction: column; padding: 22px; color: inherit; text-decoration: none; height: 100%; }
.postTop { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.category { color: var(--site-accent); font-size: .72rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }
.postArrow { color: var(--site-text-muted); }
.post h3 { margin: 0 0 10px; font-size: 1.05rem; font-weight: 650; line-height: 1.4; color: var(--site-text); }
.description { margin: 0; color: var(--site-text-muted); font-size: .82rem; line-height: 1.7; flex: 1; }
.postMeta { margin-top: 14px; color: var(--site-text-muted); font-size: .74rem; }

.closing { display: flex; align-items: center; gap: 22px; margin-bottom: 62px; border-top: 1px solid var(--site-border); border-bottom: 1px solid var(--site-border); padding: 28px 0; }
.closingMark { font-size: 2.9rem; line-height: 1; color: var(--site-accent); }
.closing h2 { margin: 0 0 8px; font-size: 1rem; font-weight: 600; }
.closing p { margin: 0; color: var(--site-text-muted); font-size: .76rem; }
.closing a { display: inline-flex; align-items: center; gap: 16px; margin-left: auto; min-height: 44px; color: var(--site-text); font-size: .8rem; white-space: nowrap; text-decoration: none; }

@media (min-width: 1600px) { .hero { padding-block: 100px; } }
@media (max-width: 996px) {
  .hero { gap: 24px; padding: 64px 0; }
  .heroText h1 { font-size: clamp(1.8rem, 3.5vw, 2.5rem); }
  .notebook { padding: 23px 24px 20px; }
  .notebookTitle { font-size: 1.9rem; }
  .gardenOrbit { inset-inline: -10px; }
  .entryGrid, .postGrid { gap: 16px; }
  .entry { padding: 20px; }
}
@media (max-width: 700px) {
  .hero, .paths, .notes, .closing { width: calc(100% - 40px); }
  .hero { grid-template-columns: 1fr; gap: 46px; padding: 44px 0 58px; }
  .heroText h1 { font-size: clamp(1.7rem, 6.5vw, 2.8rem); letter-spacing: -.045em; }
  .kicker { font-size: .72rem; margin-bottom: 20px; }
  .lead { font-size: .9rem; margin-top: 20px; }
  .garden { width: min(330px, calc(100% - 28px)); margin-inline: auto; }
  .heroFootnote { font-size: .66rem; }
  .notebookTitle { font-size: 2.05rem; }
  .entryGrid, .postGrid { grid-template-columns: 1fr; }
  .paths { padding-top: 30px; }
  .sectionHeading h2 { font-size: 1.18rem; }
  .sectionAside { display: none; }
  .entry { padding: 22px; }
  .entryTop { margin-bottom: 16px; }
  .entry p { max-width: 38em; }
  .notes { padding-bottom: 35px; }
  .closing { flex-wrap: wrap; gap: 16px; margin-bottom: 40px; }
  .closing > div { flex: 1; }
  .closing h2 { font-size: .9rem; line-height: 1.6; }
  .closing a { margin-left: 0; padding-left: 53px; }
}
@media (prefers-reduced-motion: reduce) {
  .entry, .primaryAction, .secondaryAction, .post { transition: none; }
  .entry:hover, .primaryAction:hover, .post:hover { transform: none; }
}
</style>
