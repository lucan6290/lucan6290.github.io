import React from 'react';
import Link from '@docusaurus/Link';
import {useLocation} from '@docusaurus/router';
import blogSidebars from '@site/blogSidebars';

function isActive(pathname: string, to: string) {
  return pathname === to || pathname.startsWith(`${to}/`);
}

export default function BlogSidebar() {
  const {pathname} = useLocation();

  return (
    <aside className="col col--3 blog-category-sidebar">
      <nav className="thin-scrollbar" aria-label="博客分类导航">
        <div className="blog-category-sidebar__title">博客目录</div>
        <ul className="clean-list blog-category-sidebar__list">
          <li>
            <Link
              className="blog-category-sidebar__link"
              to="/blog"
              aria-current={pathname === '/blog' ? 'page' : undefined}>
              博客首页
            </Link>
          </li>
          {blogSidebars.map((item) => (
            <li key={item.path}>
              <Link
                className="blog-category-sidebar__link"
                to={item.to}
                aria-current={isActive(pathname, item.to) ? 'page' : undefined}>
                <span>{item.label}</span>
              </Link>
              {item.items && item.items.length > 0 && (
                <ul className="clean-list blog-category-sidebar__children">
                  {item.items.map((doc) => (
                    <li key={doc.to}>
                      <Link
                        className="blog-category-sidebar__child-link"
                        to={doc.to}
                        aria-current={pathname === doc.to ? 'page' : undefined}>
                        {doc.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
