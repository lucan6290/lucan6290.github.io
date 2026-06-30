import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import styles from './about.module.css';

const focusAreas = [
  {
    title: '技术笔记',
    text: '把新技术的学习过程拆成可复盘的路径，沉淀成之后还能快速查阅的知识条目。',
  },
  {
    title: '踩坑记录',
    text: '记录环境配置、工程实践和调试过程里的问题，也保留解决问题时的判断依据。',
  },
  {
    title: '学习总结',
    text: '围绕前端、后端、AI 与基础能力做系统整理，让零散输入变成稳定的能力资产。',
  },
  {
    title: '求职经验',
    text: '整理实习准备、面试复盘和项目表达，用真实经历给之后的自己留一份参考。',
  },
];

const stackItems = ['AI 探索', '前端工程', '后端开发', 'Java 基础', '项目复盘', '面试准备'];

const contactLinks = [
  {label: 'GitHub', value: '@lucan6290', href: 'https://github.com/lucan6290'},
  {label: 'Gitee', value: '@lucan6290', href: 'https://gitee.com/lucan6290'},
  {label: 'CSDN', value: '箓川码笺', href: 'https://blog.csdn.net/2301_80165396'},
  {label: 'Email', value: 'lucan6290@gmail.com', href: 'mailto:lucan6290@gmail.com'},
];

export default function About(): React.JSX.Element {
  return (
    <Layout title="关于" description="关于箓川码笺">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>About Xiaocan Coding</p>
            <h1>把学习路上的每一次探索，写成能再次出发的笺册。</h1>
            <p className={styles.lead}>
              我是一名热爱技术的开发者，正在探索 AI、前端、后端等广阔的技术世界。
              箓川码笺用来记录学习笔记、踩坑经历、技术分享以及求职心得，让成长不只停留在当下。
            </p>
            <div className={styles.actions}>
              <Link className="button button--primary button--lg" to="/docs/intro">
                进入知识库
              </Link>
              <Link className="button button--secondary button--lg" to="/blog">
                阅读博客
              </Link>
            </div>
          </div>

          <aside className={styles.profilePanel} aria-label="站点简介">
            <div className={styles.panelTop}>
              <img src="/img/favicon.png" alt="箓川码笺" />
              <div>
                <strong>箓川码笺</strong>
                <small>记录、复盘、持续生长</small>
              </div>
            </div>
            <div className={styles.metricGrid}>
              <div>
                <strong>4</strong>
                <span>内容方向</span>
              </div>
              <div>
                <strong>6</strong>
                <span>关注主题</span>
              </div>
              <div>
                <strong>∞</strong>
                <span>长期迭代</span>
              </div>
            </div>
            <div className={styles.stackList}>
              {stackItems.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </aside>
        </section>

        <section className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Content</p>
          <h2>这里主要写什么</h2>
        </section>

        <section className={styles.focusGrid} aria-label="博客内容">
          {focusAreas.map((area, index) => (
            <article className={styles.focusCard} key={area.title}>
              <span className={styles.cardIndex}>{String(index + 1).padStart(2, '0')}</span>
              <h3>{area.title}</h3>
              <p>{area.text}</p>
            </article>
          ))}
        </section>

        <section className={styles.contactSection}>
          <div>
            <p className={styles.eyebrow}>Contact</p>
            <h2>欢迎交流</h2>
            <p>
              如果你也在学习技术、打磨项目，或正在准备实习与面试，可以从这些入口找到我。
            </p>
          </div>

          <div className={styles.contactGrid} aria-label="联系我">
            {contactLinks.map((link) => (
              <a className={styles.contactItem} href={link.href} key={link.label}>
                <span>{link.label}</span>
                <strong>{link.value}</strong>
              </a>
            ))}
          </div>
        </section>
      </main>
    </Layout>
  );
}
