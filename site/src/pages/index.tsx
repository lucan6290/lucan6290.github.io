import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import styles from './index.module.css';

const entries = [
  {
    title: '长期知识库',
    text: '沉淀技术体系、系列教程、面试复盘和可反复查阅的笔记。',
    href: '/docs/intro',
  },
  {
    title: '阶段博客',
    text: '记录项目推进、踩坑复盘、学习路径和个人成长。',
    href: '/blog',
  },
  {
    title: '项目展示',
    text: '整理实战项目、工具作品和长期维护的工程案例。',
    href: '/projects',
  },
];

export default function Home(): React.JSX.Element {
  return (
    <Layout
      title="箓川码笺"
      description="箓藏千思，川流不息">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroText}>
            <p className={styles.kicker}>箓藏千思，川流不息</p>
            <h1>箓川码笺</h1>
            <p className={styles.lead}>
              在广阔无垠的技术山川中，记录每一次探索、每一个踩坑、每一份感悟，
              将它们书写成珍贵的技术笺册，沉淀为属于自己的成长宝藏。
            </p>
            <div className={styles.actions}>
              <Link className="button button--primary button--lg" to="/docs/intro">
                进入知识库
              </Link>
              <Link className="button button--secondary button--lg" to="/blog">
                查看博客
              </Link>
            </div>
          </div>
          <div className={styles.heroPanel} aria-label="站点结构">
            <div className={styles.panelHeader}>于技术之川，拾字成箓</div>
            <div className={styles.panelLine}>docs / 技术研习 / Java 面试题</div>
            <div className={styles.panelLine}>blog / 踩坑复盘 / 成长随笔</div>
            <div className={styles.panelLine}>projects / 工程实践 / 工具作品</div>
            <div className={styles.panelLine}>about / 个人品牌 / 技术栈</div>
          </div>
        </section>

        <section className={styles.grid}>
          {entries.map((entry) => (
            <Link className={styles.entry} to={entry.href} key={entry.title}>
              <h2>{entry.title}</h2>
              <p>{entry.text}</p>
            </Link>
          ))}
        </section>
      </main>
    </Layout>
  );
}
