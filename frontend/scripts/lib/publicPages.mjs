import fs from 'node:fs';
import path from 'node:path';
import { sectionLabel } from '../../src/config/nav.ts';
import { publicPageHref, withPublicBase } from '../../src/utils/publicPaths.ts';
import { renderPublicMarkdown } from './publicMarkdown.mjs';

const SITE_NAME = '箓川码笺';
const SITE_DESCRIPTION = '箓藏千思，川流不息';
const APP_CONTAINER = '<div id="app"></div>';

function escapeMarkup(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function publicOrigin(value) {
  if (!value?.trim()) return '';
  const url = URL.parse(value.trim());
  if (!url || !['http:', 'https:'].includes(url.protocol) || url.href !== url.origin + '/') {
    throw new Error('SITE_URL 必须是 HTTP(S) origin，例如 https://example.com，部署前缀请通过 Vite base 提供。');
  }
  return url.origin;
}

function collectPages(manifest) {
  const pages = new Map([['/', { title: SITE_NAME, children: manifest.tree.filter(node => !node.article) }]]);
  function visit(nodes, top = false) {
    for (const node of nodes) {
      // Vue 固定路由覆盖 /about，内容路由只展示一级目录下的文章。
      if (top && (node.article || node.path === '/about')) continue;
      const { article, introduction, children } = node;
      pages.set(node.path, {
        title: top ? sectionLabel(node.name) : node.label,
        description: article?.excerpt || introduction?.excerpt,
        article,
        introduction,
        children,
      });
      visit(children);
    }
  }
  visit(manifest.tree, true);
  return pages;
}

function pageBody(page, route, base, assets) {
  const href = value => escapeMarkup(publicPageHref(value, base));
  const source = page.article || page.introduction;
  const markdown = source ? renderPublicMarkdown(source, { base, assets, title: page.title }) : '';
  const children = page.children?.map(node => `<li><a href="${href(node.path)}">${escapeMarkup(node.label)}</a></li>`).join('');
  const parent = route.slice(0, route.lastIndexOf('/'));
  const nav = route === '/' ? '' : `<nav aria-label="页面位置"><a href="${href('/')}">首页</a>${parent ? ` · <a href="${href(parent)}">上一级</a>` : ''}</nav>`;
  const title = escapeMarkup(page.title);
  return `<main class="prerendered-page">${nav}<article class="markdown-body"><h1>${title}</h1>${markdown}${children ? `<ul>${children}</ul>` : ''}</article></main>`;
}

function pageHtml(template, { title, description, article }, route, origin, base, body) {
  const headline = route === '/' ? SITE_NAME : `${title} - ${SITE_NAME}`;
  const summary = description || SITE_DESCRIPTION;
  const absolute = origin ? origin + publicPageHref(route, base) : '';
  const escape = escapeMarkup;
  const head = [
    `<meta property="og:type" content="${article ? 'article' : 'website'}">`,
    `<meta property="og:title" content="${escape(headline)}">`,
    `<meta property="og:description" content="${escape(summary)}">`,
    ...(absolute ? [
      `<link rel="canonical" href="${escape(absolute)}">`,
      `<meta property="og:url" content="${escape(absolute)}">`,
      `<link rel="alternate" type="application/rss+xml" title="${SITE_NAME} · 博客" href="${escape(origin + withPublicBase('/rss.xml', base))}">`,
    ] : []),
  ];
  return template
    .replace(/<title>[^<]*<\/title>/, () => `<title>${escape(headline)}</title>`)
    .replace(/<meta name="description"[^>]*>/, () => `<meta name="description" content="${escape(summary)}">`)
    .replace('</head>', () => head.join('\n    ') + '\n  </head>')
    .replace(APP_CONTAINER, () => `<div id="app">${body}</div>`);
}

function writeFeeds(outDir, pages, origin, base) {
  const absolute = route => escapeMarkup(origin + publicPageHref(route, base));
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  const urls = [];
  const items = [];
  for (const [route, page] of pages) {
    const updated = Date.parse(page.article?.frontmatter.updated);
    const lastmod = Number.isFinite(updated) ? `<lastmod>${new Date(updated).toISOString()}</lastmod>` : '';
    urls.push(`<url><loc>${absolute(route)}</loc>${lastmod}</url>`);
    const published = Date.parse(page.article?.frontmatter.date);
    if (route.startsWith('/blog/') && Number.isFinite(published)) items.push({ route, page, published });
  }
  items.sort((a, b) => b.published - a.published || (a.route < b.route ? -1 : Number(a.route > b.route)));
  const entries = items.map(({ route, page, published }) => `<item>
  <title>${escapeMarkup(page.title)}</title><link>${absolute(route)}</link><guid>${absolute(route)}</guid>
  <description>${escapeMarkup(page.description || '')}</description><pubDate>${new Date(published).toUTCString()}</pubDate>
</item>`);
  const self = escapeMarkup(origin + withPublicBase('/rss.xml', base));
  fs.writeFileSync(path.join(outDir, 'sitemap.xml'), xml + `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`);
  fs.writeFileSync(path.join(outDir, 'rss.xml'), xml + `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>${SITE_NAME} · 博客</title><link>${absolute('/')}</link><description>${SITE_DESCRIPTION}</description><language>zh-CN</language>
<atom:link href="${self}" rel="self" type="application/rss+xml"/>
${entries.join('\n')}
</channel></rss>\n`);
}

export function writePublicPages({ outDir, manifest, base, siteUrl, assets = {}, warn = console.warn }) {
  const origin = publicOrigin(siteUrl);
  if (!base.startsWith('/') || base.startsWith('//')) {
    throw new Error('静态页面构建需要绝对路径形式的 Vite base，例如 / 或 /xiaocancoding/。');
  }
  if (!origin) warn('[public-pages] 未设置 SITE_URL，已跳过 canonical、sitemap.xml 和 rss.xml。');
  const root = path.resolve(outDir);
  const template = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  if (!template.includes(APP_CONTAINER)) throw new Error('静态页面模板缺少 Vue 挂载容器。');
  const pages = collectPages(manifest);
  for (const [route, page] of pages) {
    const target = path.resolve(root, '.' + route, 'index.html');
    if (!target.startsWith(root + path.sep)) throw new Error(`页面路径超出构建目录：${route}`);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, pageHtml(template, page, route, origin, base, pageBody(page, route, base, assets)));
  }
  if (origin) writeFeeds(root, pages, origin, base);
  return pages.size;
}
