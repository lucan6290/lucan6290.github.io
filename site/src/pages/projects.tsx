import React from 'react';
import Layout from '@theme/Layout';

const projects = [
  {
    name: '个人技术站',
    description: '基于 Docusaurus 的长期知识库、博客与项目展示站。',
  },
  {
    name: '内容管理端',
    description: '面向 Markdown 写作的本地 Admin，用于创建、编辑和管理站点内容。',
  },
];

export default function Projects(): React.JSX.Element {
  return (
    <Layout title="项目" description="项目展示">
      <main className="page-shell">
        <section className="simple-page">
          <p className="eyebrow">Projects</p>
          <h1>项目展示</h1>
          <div className="project-list">
            {projects.map((project) => (
              <article className="project-item" key={project.name}>
                <h2>{project.name}</h2>
                <p>{project.description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </Layout>
  );
}

