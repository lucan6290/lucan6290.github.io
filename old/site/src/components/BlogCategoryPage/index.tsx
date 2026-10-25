import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import BlogSidebar from '@theme/BlogSidebar';
import {
  HtmlClassNameProvider,
  PageMetadata,
  ThemeClassNames,
} from '@docusaurus/theme-common';

type BlogCategory = {
  label: string;
  path: string;
  to: string;
  count?: number;
};

type BlogCategoryPost = {
  title: string;
  description?: string;
  date?: string;
  permalink: string;
  tags?: string[];
};

type BlogCategoryData = {
  category: BlogCategory;
  posts: BlogCategoryPost[];
};

type Props = {
  categoryData: BlogCategoryData;
};

function formatDate(date: string | undefined) {
  if (!date) {
    return '';
  }
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return date;
  }
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(parsed);
}

function BlogCategoryPostList({posts}: {posts: BlogCategoryPost[]}) {
  if (posts.length === 0) {
    return <p className="blog-category-empty">这个分类下还没有文章。</p>;
  }

  return (
    <div className="blog-category-list">
      {posts.map((post) => (
        <article className="blog-category-item" key={post.permalink}>
          <header>
            <h2>
              <Link to={post.permalink}>{post.title}</Link>
            </h2>
            {post.date && <time dateTime={post.date}>{formatDate(post.date)}</time>}
          </header>
          {post.description && <p>{post.description}</p>}
          {post.tags && post.tags.length > 0 && (
            <div className="blog-category-tags">
              {post.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

export default function BlogCategoryPage({categoryData}: Props) {
  const {category, posts} = categoryData;

  return (
    <HtmlClassNameProvider
      className={clsx(
        ThemeClassNames.wrapper.blogPages,
        ThemeClassNames.page.blogListPage,
      )}>
      <PageMetadata
        title={`${category.label} - 博客`}
        description={`博客分类：${category.label}`}
      />
      <Layout>
        <div className="container margin-vert--lg">
          <div className="row">
            <BlogSidebar sidebar={{title: '博客目录', items: []}} />
            <main className="col col--7">
              <section className="blog-category-page">
                <header className="blog-category-header">
                  <p>博客分类</p>
                  <h1>{category.label}</h1>
                </header>
                <BlogCategoryPostList posts={posts} />
              </section>
            </main>
          </div>
        </div>
      </Layout>
    </HtmlClassNameProvider>
  );
}
