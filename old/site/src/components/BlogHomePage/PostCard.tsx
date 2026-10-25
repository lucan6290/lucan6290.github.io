import React from 'react';
import Link from '@docusaurus/Link';
import {formatPostDate, type BlogSummary} from './content';
import styles from './styles.module.css';

export default function PostCard({post}: {post: BlogSummary}): React.JSX.Element {
  return (
    <article className={styles.post}>
      <Link to={post.permalink} className={styles.postLink}>
        <div className={styles.postTop}>
          <span className={styles.category}>{post.category || '随手记录'}</span>
          <span className={styles.postArrow} aria-hidden="true">↗</span>
        </div>
        <h3>{post.title}</h3>
        {post.description && <p className={styles.description}>{post.description}</p>}
        <div className={styles.postMeta}>
          {post.date && <time dateTime={post.date}>{formatPostDate(post.date)}</time>}
          {post.readingTime != null && (
            <span>约 {Math.max(1, Math.ceil(post.readingTime))} 分钟阅读</span>
          )}
        </div>
      </Link>
    </article>
  );
}
