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
        <div class="section-heading"><div><p class="section-kicker">记录与分享</p><h2 id="focus-title">为什么建这个站</h2></div></div>
        <p class="focus-lead">我想把零散的学习笔记、踩坑过程和项目经验整理在一起，方便日后查找与总结，也分享给同样在学习技术的在校学生。这里既有持续修订的知识笔记，也有项目实践和阶段性思考。</p>
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
            <p class="project-role">{{ project.role }}</p>
            <a v-if="project.external" :href="project.href" target="_blank" rel="noopener noreferrer" class="project-link">{{ project.linkLabel }} <span aria-hidden="true">↗</span></a>
            <router-link v-else :to="project.href" class="project-link">{{ project.linkLabel }} <span aria-hidden="true">↗</span></router-link>
          </article>
        </div>
      </section>

      <section class="personal" aria-labelledby="personal-title">
        <div><p class="section-kicker">屏幕之外</p><h2 id="personal-title">也在路上</h2></div>
        <p>技术之外，我喜欢旅游、阅读、骑行和自驾游。希望将来自驾去新疆和西藏，也走一走独库公路。</p>
      </section>

      <section class="contact" aria-labelledby="contact-title">
        <div class="contact-copy"><p class="section-kicker">保持联系</p><h2 id="contact-title">欢迎交流</h2><p>欢迎交流技术学习、项目实践、文章勘误与合作。反馈问题时，请附上原文或报错链接、运行环境与复现步骤；合作联系请简单介绍背景和想法。</p></div>
        <div class="contact-list" aria-label="联系我">
          <a v-for="item in contacts" :key="item.label" :href="item.href"><span>{{ item.label }}</span><strong>{{ item.value }}</strong><span class="contact-symbol" aria-hidden="true">↗</span></a>
        </div>
      </section>

      <section class="site-notes" aria-labelledby="site-notes-title">
        <div class="section-heading"><div><p class="section-kicker">站点说明</p><h2 id="site-notes-title">转载、许可与隐私</h2></div></div>
        <dl class="site-notes-list">
          <div><dt>文章转载</dt><dd>转载本站原创文章时，请注明“箓川码笺”及原文链接。</dd></div>
          <div><dt>代码许可</dt><dd>本站源代码采用 <a href="https://choosealicense.com/licenses/mit/" target="_blank" rel="noopener noreferrer">MIT 许可</a>；原创文章、笔记和图片不在该许可范围内。</dd></div>
          <div><dt>隐私与统计</dt><dd>当前前端仅在浏览器本地保存主题和侧栏偏好，尚未接入访问统计。统计工具确定并启用后，会在这里说明服务方及实际数据处理方式。</dd></div>
          <div><dt>商业内容</dt><dd>目前没有广告、赞助或联盟链接；如将来加入，会明确标注。</dd></div>
          <div><dt>站点源码</dt><dd><a href="https://github.com/lucan6290/lucan6290.github.io" target="_blank" rel="noopener noreferrer">查看 GitHub 仓库</a></dd></div>
          <div><dt>最近更新</dt><dd><time datetime="2026-10-27">2026 年 10 月 27 日</time></dd></div>
        </dl>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
const stack = ['AI 工具实践', '开发工具', '算法与基础', '个人技术站', '部署运维', '技术表达'];
const focusAreas = [
  { title: '内容从哪里来', text: '来自日常学习、项目实践、问题排查时写下的笔记，以及阶段性的经验复盘。' },
  { title: '怎样写成文章', text: '先记录问题的场景、尝试与结果，再查阅资料、验证做法，整理成方便回看的内容。' },
  { title: '怎样看待结论', text: '尽量区分亲自实践、资料学习和个人判断；技术内容会随着新的实践持续修订。' },
  { title: '发现错误', text: '欢迎通过邮箱提供文章链接、运行环境和复现步骤，方便我核对并修正。' },
];
const projects = [
  { label: '个人技术站', title: '箓川码笺', text: '基于 Vite 与 Vue 3 自研前端，承载长期知识库、博客与项目展示。', role: '我负责前端实现、内容结构和持续迭代。', href: 'https://github.com/lucan6290/lucan6290.github.io', linkLabel: '查看站点仓库', external: true },
  { label: '内容管理', title: '本地 Markdown 管理端', text: '面向 Markdown 写作维护站点内容，记录编辑、管理与发布流程。', role: '我负责管理端开发与内容工作流梳理。', href: '/projects', linkLabel: '查看项目列表', external: false },
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
.section-heading h2, .contact h2, .personal h2 { font-size: 1.65rem; line-height: 1.3; }
.focus-lead { max-width: 760px; margin-bottom: 30px; color: var(--site-text-secondary); font-size: .96rem; line-height: 1.9; }
.focus-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 56px; }
.focus-item { padding: 22px 0; border-top: 1px solid var(--site-border); }
.focus-item h3 { color: var(--site-text); font-size: 1.08rem; margin-bottom: 8px; }
.focus-item p, .contact-copy > p:last-child { color: var(--site-text-secondary); font-size: .93rem; line-height: 1.85; }
.project-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 56px; }
.project-item { padding: 20px 0; border-top: 1px solid var(--site-border); }
.project-label { margin-bottom: 7px; color: var(--site-accent-ink); font-size: .78rem; font-weight: 650; }
.project-item h3 { margin: 0 0 8px; color: var(--site-text); font-size: 1.08rem; }
.project-item > p:not(.project-label) { color: var(--site-text-secondary); font-size: .93rem; line-height: 1.85; }
.project-item .project-role { margin-top: 10px; }
.project-more { display: inline-flex; gap: 10px; align-items: center; color: var(--site-accent-ink); font-size: .88rem; font-weight: 650; }
.project-link { display: inline-flex; gap: 8px; margin-top: 14px; color: var(--site-accent-ink); font-size: .88rem; font-weight: 650; }
.personal { display: grid; grid-template-columns: .9fr 1.1fr; gap: 100px; padding: 64px 0; border-bottom: 1px solid var(--site-border); }
.personal > p { max-width: 580px; color: var(--site-text-secondary); font-size: .96rem; line-height: 1.9; }
.contact { display: grid; grid-template-columns: .9fr 1.1fr; gap: 100px; padding: 72px 0; border-bottom: 1px solid var(--site-border); }
.contact-copy > p:last-child { margin-top: 14px; max-width: 360px; }
.contact-list { border-top: 1px solid var(--site-border); }
.contact-list a { display: grid; grid-template-columns: 80px minmax(0, 1fr) auto; align-items: center; gap: 16px; min-height: 60px; border-bottom: 1px solid var(--site-border); color: var(--site-text); text-decoration: none; }
.contact-list a > span:first-child { color: var(--site-text-muted); font-size: .88rem; }
.contact-list strong { font-size: .92rem; font-weight: 600; overflow-wrap: anywhere; }
.contact-symbol { color: var(--site-text-muted); }
.contact-list a:hover, .contact-list a:hover .contact-symbol { color: var(--site-accent-ink); }
.site-notes { padding-top: 72px; }
.site-notes-list { margin: 0; border-top: 1px solid var(--site-border); }
.site-notes-list > div { display: grid; grid-template-columns: 150px minmax(0, 1fr); gap: 24px; padding: 18px 0; border-bottom: 1px solid var(--site-border); }
.site-notes-list dt { font-weight: 650; }
.site-notes-list dd { margin: 0; color: var(--site-text-secondary); font-size: .93rem; line-height: 1.85; }
.site-notes-list a { color: var(--site-accent-ink); }
.action:focus-visible, .project-link:focus-visible, .contact-list a:focus-visible, .site-notes-list a:focus-visible { outline: 2px solid var(--site-accent); outline-offset: 3px; }
@media (max-width: 850px) { .intro { grid-template-columns: 1fr; gap: 36px; padding-bottom: 56px; } .identity { max-width: 520px; } .focus, .projects { padding: 56px 0; } .personal { gap: 40px; padding: 56px 0; } .contact { gap: 40px; padding: 56px 0; } .site-notes { padding-top: 56px; } }
@media (max-width: 600px) { .about-page { padding: 48px 20px 72px; } .desktop-break { display: none; } .intro h1 { font-size: clamp(1.9rem, 8vw, 2.5rem); } .section-heading { display: block; } .focus-grid, .project-grid, .personal, .contact { grid-template-columns: 1fr; } .focus-item, .project-item { padding: 18px 0; } .personal, .contact { gap: 28px; } .contact-list a { grid-template-columns: 65px minmax(0, 1fr) auto; gap: 10px; } .site-notes-list > div { grid-template-columns: 1fr; gap: 4px; } }
</style>
