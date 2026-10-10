<template>
  <main class="page">
    <section class="hero">
      <div class="heroCopy">
        <p class="eyebrow">About Xiaocan Coding</p>
        <h1>把学习路上的每一次探索，写成能再次出发的笺册。</h1>
        <p class="lead">我是一名热爱技术的开发者，正在探索 AI、前端、后端等广阔的技术世界。箓川码笺用来记录学习笔记、踩坑经历、技术分享以及求职心得，让成长不只停留在当下。</p>
        <div class="actions">
          <router-link class="button primary" to="/knowledge">进入知识库</router-link>
          <router-link class="button secondary" to="/blog">阅读博客</router-link>
        </div>
      </div>
      <aside class="profilePanel" aria-label="站点简介">
        <div class="panelTop">
          <div class="avatar" aria-hidden="true">箓</div>
          <div><strong>箓川码笺</strong><small>记录、复盘、持续生长</small></div>
        </div>
        <div class="metricGrid">
          <div><strong>4</strong><span>内容方向</span></div>
          <div><strong>6</strong><span>关注主题</span></div>
          <div><strong>∞</strong><span>长期迭代</span></div>
        </div>
        <div class="stackList">
          <span v-for="s in stack" :key="s">{{ s }}</span>
        </div>
      </aside>
    </section>

    <section class="sectionHeader"><p class="eyebrow">Content</p><h2>这里主要写什么</h2></section>
    <section class="focusGrid" aria-label="博客内容">
      <article v-for="(area, i) in focusAreas" :key="area.title" class="focusCard">
        <span class="cardIndex">{{ String(i + 1).padStart(2, '0') }}</span>
        <h3>{{ area.title }}</h3>
        <p>{{ area.text }}</p>
      </article>
    </section>

    <section class="contactSection">
      <div><p class="eyebrow">Contact</p><h2>欢迎交流</h2><p>如果你也在学习技术、打磨项目，或正在准备实习与面试，可以从这些入口找到我。</p></div>
      <div class="contactGrid" aria-label="联系我">
        <a v-for="l in contacts" :key="l.label" class="contactItem" :href="l.href">
          <span>{{ l.label }}</span><strong>{{ l.value }}</strong>
        </a>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
const stack = ['AI 探索', '前端工程', '后端开发', 'Java 基础', '项目复盘', '面试准备'];
const focusAreas = [
  { title: '技术笔记', text: '把新技术的学习过程拆成可复盘的路径，沉淀成之后还能快速查阅的知识条目。' },
  { title: '踩坑记录', text: '记录环境配置、工程实践和调试过程里的问题，也保留解决问题时的判断依据。' },
  { title: '学习总结', text: '围绕前端、后端、AI 与基础能力做系统整理，让零散输入变成稳定的能力资产。' },
  { title: '求职经验', text: '整理实习准备、面试复盘和项目表达，用真实经历给之后的自己留一份参考。' },
];
const contacts = [
  { label: 'GitHub', value: '@lucan6290', href: 'https://github.com/lucan6290' },
  { label: 'Gitee', value: '@lucan6290', href: 'https://gitee.com/lucan6290' },
  { label: 'CSDN', value: '箓川码笺', href: 'https://blog.csdn.net/2301_80165396' },
  { label: 'Email', value: 'lucan6290@gmail.com', href: 'mailto:lucan6290@gmail.com' },
];
</script>

<style scoped>
.page { min-height: calc(100vh - var(--ifm-navbar-height)); background: linear-gradient(135deg, rgba(31,111,235,0.08) 0 1px, transparent 1px 28px), linear-gradient(180deg, #f7fafc 0%, #ffffff 38%, #f8fbff 100%); color: var(--site-text); padding: 70px 24px 96px; }
html[data-theme='dark'] .page { background: var(--site-background); }
.hero { display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.72fr); gap: 46px; align-items: stretch; width: min(1120px, 100%); margin: 0 auto; }
.heroCopy { position: relative; border-left: 4px solid var(--ifm-color-primary); padding: 10px 0 12px 30px; }
.eyebrow { margin: 0 0 14px; color: var(--ifm-color-primary); font-family: var(--ifm-font-family-monospace); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.hero h1 { max-width: 760px; margin: 0; color: var(--site-text); font-size: clamp(2.45rem, 5vw, 4.4rem); line-height: 1.06; text-wrap: balance; }
.lead { margin: 22px 0 0; color: var(--site-text-secondary); font-size: 1.05rem; line-height: 1.85; max-width: 680px; }
.actions { display: flex; gap: 16px; margin-top: 28px; flex-wrap: wrap; }
.button { display: inline-flex; align-items: center; justify-content: center; min-height: 46px; padding: 0 24px; border-radius: 7px; font-weight: 700; font-size: 0.95rem; text-decoration: none; transition: background 180ms, transform 180ms; }
.button.primary { background: var(--ifm-color-primary); color: var(--site-on-accent); }
.button.primary:hover { background: var(--ifm-color-primary-dark); transform: translateY(-2px); }
.button.secondary { border: 1px solid var(--site-border); color: var(--site-text); }
.button.secondary:hover { border-color: var(--ifm-color-primary); color: var(--ifm-color-primary); }

.profilePanel { border: 1px solid var(--site-border); border-radius: 12px; background: var(--site-surface); padding: 28px; display: flex; flex-direction: column; gap: 22px; }
.panelTop { display: flex; align-items: center; gap: 16px; }
.avatar { width: 56px; height: 56px; border-radius: 12px; background: var(--site-accent-soft); color: var(--site-accent); display: grid; place-items: center; font-size: 1.6rem; font-weight: 800; font-family: var(--site-font-literary); }
.panelTop strong { display: block; font-size: 1.05rem; color: var(--site-text); }
.panelTop small { color: var(--site-text-muted); font-size: 0.82rem; }
.metricGrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 16px 0; border-top: 1px solid var(--site-border); border-bottom: 1px solid var(--site-border); text-align: center; }
.metricGrid strong { display: block; font-size: 1.4rem; color: var(--site-text); }
.metricGrid span { font-size: 0.78rem; color: var(--site-text-muted); }
.stackList { display: flex; flex-wrap: wrap; gap: 8px; }
.stackList span { padding: 4px 10px; border-radius: 999px; background: var(--site-accent-soft); color: var(--ifm-color-primary); font-size: 0.78rem; font-weight: 600; }

.sectionHeader { width: min(1120px, 100%); margin: 64px auto 24px; }
.sectionHeader h2 { margin: 0; font-size: 1.6rem; }
.focusGrid { width: min(1120px, 100%); margin: 0 auto; display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.focusCard { border: 1px solid var(--site-border); border-radius: 10px; background: var(--site-surface); padding: 26px; }
.cardIndex { color: var(--site-text-muted); font-family: var(--ifm-font-family-monospace); font-size: 0.72rem; letter-spacing: 0.1em; }
.focusCard h3 { margin: 10px 0 8px; font-size: 1.1rem; color: var(--site-text); }
.focusCard p { margin: 0; color: var(--site-text-secondary); font-size: 0.92rem; line-height: 1.75; }

.contactSection { width: min(1120px, 100%); margin: 64px auto 0; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: start; }
.contactSection h2 { margin: 0 0 12px; font-size: 1.6rem; }
.contactSection p { color: var(--site-text-secondary); line-height: 1.75; }
.contactGrid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.contactItem { display: flex; flex-direction: column; gap: 4px; padding: 18px; border: 1px solid var(--site-border); border-radius: 10px; background: var(--site-surface); text-decoration: none; transition: border-color 180ms; }
.contactItem:hover { border-color: var(--ifm-color-primary); }
.contactItem span { color: var(--site-text-muted); font-size: 0.78rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
.contactItem strong { color: var(--site-text); font-size: 1rem; }

@media (max-width: 996px) {
  .hero { grid-template-columns: 1fr; }
  .focusGrid, .contactSection { grid-template-columns: 1fr; }
  .contactGrid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .contactGrid { grid-template-columns: 1fr; }
}
</style>
