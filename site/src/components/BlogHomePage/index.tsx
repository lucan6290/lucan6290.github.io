import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {
  HtmlClassNameProvider,
  PageMetadata,
  ThemeClassNames,
} from '@docusaurus/theme-common';
import BlogLayout from '@theme/BlogLayout';
import SearchMetadata from '@theme/SearchMetadata';
import BlogHomeContent from '@site/blog/index.md';
import type {Props} from '@theme/BlogListPage';

function BlogHomePageMetadata({metadata}: Props): ReactNode {
  const {
    siteConfig: {title: siteTitle},
  } = useDocusaurusContext();
  const {blogDescription, blogTitle, permalink} = metadata;
  const isBlogOnlyMode = permalink === '/';
  const title = isBlogOnlyMode ? siteTitle : blogTitle;

  return (
    <>
      <PageMetadata title={title} description={blogDescription} />
      <SearchMetadata tag="blog_posts_list" />
    </>
  );
}

export default function BlogHomePage(props: Props): ReactNode {
  const {sidebar} = props;

  return (
    <HtmlClassNameProvider
      className={clsx(
        ThemeClassNames.wrapper.blogPages,
        ThemeClassNames.page.blogListPage,
      )}>
      <BlogHomePageMetadata {...props} />
      <BlogLayout sidebar={sidebar}>
        <section className="blog-home-content markdown">
          <BlogHomeContent />
        </section>
      </BlogLayout>
    </HtmlClassNameProvider>
  );
}
