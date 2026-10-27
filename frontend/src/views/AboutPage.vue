<template>
  <main class="about-page">
    <div class="about-wrap">
      <section class="intro" aria-labelledby="about-title">
        <div class="intro-copy">
          <p class="intro-kicker"><span aria-hidden="true"></span>关于箓川码笺</p>
          <h1 id="about-title">把学习路上的每一次探索，<br class="desktop-break">写成能再次出发的笺册。</h1>
          <p class="intro-text">我是箓川码笺的作者“小灿同学啊”，持续记录 AI 工具实践、开发工具与计算机基础学习，也分享个人技术站建设中的问题复盘和工程经验。</p>
          <div class="intro-actions">
            <router-link class="action action-primary" to="/knowledge">进入知识库</router-link>
            <router-link class="action action-secondary" to="/blog">阅读博客</router-link>
          </div>
        </div>
        <aside class="identity" aria-label="站点简介">
          <div class="identity-heading"><span class="seal" aria-hidden="true">箓</span><div><strong>箓川码笺</strong><p>记录、复盘、持续生长</p></div></div>
          <div class="identity-rule"></div>
          <p class="identity-label">关注的主题</p>
          <div class="topics"><span v-for="item in stack" :key="item">{{ item }}</span></div>
        </aside>
      </section>

      <section class="focus" aria-labelledby="focus-title">
        <div class="section-heading"><div><p class="section-kicker">记录与分享</p><h2 id="focus-title">这里主要写什么</h2></div><p>从一次尝试，到一份可以再次查阅的记录。</p></div>
        <div class="focus-grid">
          <article v-for="area in focusAreas" :key="area.title" class="focus-item"><h3>{{ area.title }}</h3><p>{{ area.text }}</p></article>
        </div>
      </section>

      <section class="projects" aria-labelledby="projects-title">
        <div class="section-heading">
          <div><p class="section-kicker">工程实践</p><h2 id="projects-title">正在建设的项目</h2></div>
          <router-link class="project-more" to="/projects">查看项目 <span aria-hidden="true">↗</span></router-link>
        </div>
        <div class="project-grid">
          <article v-for="project in projects" :key="project.title" class="project-item">
            <p class="project-label">{{ project.label }}</p>
            <h3>{{ project.title }}</h3>
            <p>{{ project.text }}</p>
          </article>
        </div>
      </section>

      <section class="contact" aria-labelledby="contact-title">
        <div class="contact-copy"><p class="section-kicker">保持联系</p><h2 id="contact-title">欢迎交流</h2><p>如果你也在学习技术、打磨项目，或正在准备实习与面试，可以从这些入口找到我。</p></div>
        <div class="contact-list" aria-label="联系我">
          <a v-for="item in contacts" :key="item.label" :href="item.href"><span>{{ item.label }}</span><strong>{{ item.value }}</strong><span class="contact-symbol" aria-hidden="true">↗</span></a>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
const stack = ['AI 工具实践', '开发工具', '算法与基础', '个人技术站', '部署运维', '技术表达'];
const focusAreas = [
  { title: 'AI 工具实践', text: '记录 Cursor、Claude Code 等工具的真实体验，以及 AI 对开发流程和工作的影响。' },
  { title: '技术研习', text: '围绕开发工具、算法与计算机基础整理可回看、可持续更新的笔记。' },
  { title: '工程实践', text: '分享自研技术站、内容管理端和部署运维过程中的实现、取舍与问题复盘。' },
  { title: '技术表达', text: '复盘“看得懂却讲不清”的原因，整理技术总结与表达训练的方法。' },
];
const projects = [
  { label: '个人技术站', title: '箓川码笺', text: '基于 Vite 与 Vue 3 自研前端，承载长期知识库、博客与项目展示。' },
  { label: '内容管理', title: '本地 Markdown 管理端', text: '面向 Markdown 写作维护站点内容，记录编辑、管理与发布流程。' },
];
const contacts = [
  { label: 'GitHub', value: '@lucan6290', href: 'https://github.com/lucan6290' },
  { label: 'Gitee', value: '@lucan6290', href: 'https://gitee.com/lucan6290' },
  { label: 'CSDN', value: '小灿同学啊', href: 'https://blog.csdn.net/2301_80165396' },
  { label: 'Email', value: 'lucan6290@gmail.com', href: 'mailto:lucan6290@gmail.com' },
];
</script>

<style scoped>
.about-page { min-height: calc(100vh - var(--ifm-navbar-height)); background: var(--site-background); color: var(--site-text); padding: 80px 28px 104px; --about-action-bg: #1f6feb; --about-action-bg-hover: #175dcc; --about-action-ink: #ffffff; }
:global(html[data-theme='dark'] .about-page) { --about-action-bg: var(--site-accent); --about-action-bg-hover: var(--site-accent-hover); --about-action-ink: var(--site-on-accent); }
.about-wrap { width: min(1100px, 100%); margin: 0 auto; }
.intro { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(250px, .72fr); gap: 68px; align-items: center; padding-bottom: 76px; border-bottom: 1px solid var(--site-border); }
.intro-kicker, .section-kicker { color: var(--site-accent-ink); font-size: .88rem; font-weight: 700; letter-spacing: .04em; }
.intro-kicker { display: flex; align-items: center; gap: 10px; margin-bottom: 22px; }
.intro-kicker span { width: 24px; height: 2px; background: var(--site-accent); }
.intro h1 { margin: 0; font-family: var(--site-font-literary); font-size: clamp(2.05rem, 3.25vw, 3.1rem); font-weight: 700; line-height: 1.36; letter-spacing: -.025em; }
.intro-text { max-width: 620px; margin-top: 22px; color: var(--site-text-secondary); font-size: 1rem; line-height: 1.9; }
.intro-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; }
.action { min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: 0 19px; border: 1px solid transparent; border-radius: 7px; font-weight: 700; font-size: .9rem; text-decoration: none; }
.action-primary { color: var(--about-action-ink); background: var(--about-action-bg); }
.action-primary:hover { background: var(--about-action-bg-hover); color: var(--about-action-ink); }
.action-secondary { border-color: var(--site-border); color: var(--site-text); background: var(--site-surface); }
.action-secondary:hover { color: var(--site-accent-ink); border-color: var(--site-accent); }
.identity { padding: 28px; border: 1px solid var(--site-border); border-radius: 12px; background: var(--site-surface); box-shadow: 0 16px 40px var(--site-shadow); }
.identity-heading { display: flex; align-items: center; gap: 14px; }
.seal { display: grid; place-items: center; width: 52px; height: 52px; flex: none; border-radius: 10px; color: var(--site-accent-ink); background: var(--site-accent-soft); font: 700 1.55rem var(--site-font-literary); }
.identity-heading strong { font-size: 1.05rem; }
.identity-heading p { margin-top: 3px; color: var(--site-text-muted); font-size: .84rem; }
.identity-rule { height: 1px; margin: 23px 0; background: var(--site-border); }
.identity-label { margin-bottom: 12px; color: var(--site-text-muted); font-size: .85rem; }
.topics { display: flex; flex-wrap: wrap; gap: 8px; }
.topics span { padding: 4px 10px; border: 1px solid var(--site-border); border-radius: 6px; color: var(--site-text-secondary); font-size: .82rem; }
.focus { padding: 72px 0; border-bottom: 1px solid var(--site-border); }
.projects { padding: 64px 0; border-bottom: 1px solid var(--site-border); }
.section-heading { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 28px; }
.section-kicker { margin-bottom: 8px; }
.section-heading h2, .contact h2 { font-size: 1.65rem; line-height: 1.3; }
.section-heading > p { color: var(--site-text-muted); font-size: .9rem; }
.focus-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 56px; }
.focus-item { padding: 22px 0; border-top: 1px solid var(--site-border); }
.focus-item h3 { color: var(--site-text); font-size: 1.08rem; margin-bottom: 8px; }
.focus-item p, .contact-copy > p:last-child { color: var(--site-text-secondary); font-size: .93rem; line-height: 1.85; }
.project-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 56px; }
.project-item { padding: 20px 0; border-top: 1px solid var(--site-border); }
.project-label { margin-bottom: 7px; color: var(--site-accent-ink); font-size: .78rem; font-weight: 650; }
.project-item h3 { margin: 0 0 8px; color: var(--site-text); font-size: 1.08rem; }
.project-item > p:last-child { color: var(--site-text-secondary); font-size: .93rem; line-height: 1.85; }
.project-more { display: inline-flex; gap: 10px; align-items: center; color: var(--site-accent-ink); font-size: .88rem; font-weight: 650; }
.contact { display: grid; grid-template-columns: .9fr 1.1fr; gap: 100px; padding-top: 72px; }
.contact-copy > p:last-child { margin-top: 14px; max-width: 360px; }
.contact-list { border-top: 1px solid var(--site-border); }
.contact-list a { display: grid; grid-template-columns: 80px minmax(0, 1fr) auto; align-items: center; gap: 16px; min-height: 60px; border-bottom: 1px solid var(--site-border); color: var(--site-text); text-decoration: none; }
.contact-list a > span:first-child { color: var(--site-text-muted); font-size: .88rem; }
.contact-list strong { font-size: .92rem; font-weight: 600; overflow-wrap: anywhere; }
.contact-symbol { color: var(--site-text-muted); }
.contact-list a:hover, .contact-list a:hover .contact-symbol { color: var(--site-accent-ink); }
.action:focus-visible, .contact-list a:focus-visible { outline: 2px solid var(--site-accent); outline-offset: 3px; }
@media (max-width: 850px) { .intro { grid-template-columns: 1fr; gap: 36px; padding-bottom: 56px; } .identity { max-width: 520px; } .focus, .projects { padding: 56px 0; } .contact { gap: 40px; padding-top: 56px; } }
@media (max-width: 600px) { .about-page { padding: 48px 20px 72px; } .desktop-break { display: none; } .intro h1 { font-size: clamp(1.9rem, 8vw, 2.5rem); } .section-heading { display: block; } .section-heading > p { margin-top: 10px; } .focus-grid, .project-grid, .contact { grid-template-columns: 1fr; } .focus-item, .project-item { padding: 18px 0; } .contact { gap: 28px; } .contact-list a { grid-template-columns: 65px minmax(0, 1fr) auto; gap: 10px; } }
</style>
