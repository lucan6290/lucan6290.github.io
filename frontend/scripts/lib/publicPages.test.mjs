import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { build } from './buildContent.mjs';

const shell = '<!doctype html><html><head><title>箓川码笺</title><meta name="description" content="箓藏千思，川流不息" /></head><body><div id="app"></div><script type="module" src="/repo/assets/app.js"></script></body></html>';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'public-pages-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const outDir = path.join(root, 'dist');
  fs.mkdirSync(path.join(contentDir, 'blog'), { recursive: true });
  fs.mkdirSync(outDir);
  fs.writeFileSync(path.join(outDir, 'index.html'), shell);
  fs.writeFileSync(path.join(contentDir, 'blog.md'), '# 首页同名文章');
  fs.writeFileSync(path.join(contentDir, 'blog', 'README.md'), '# 博客介绍\n\n站点文章。');
  fs.writeFileSync(path.join(contentDir, 'blog', '文章 #1.md'), [
    '---', 'title: "文章 & 笔记"', 'date: "2026-10-29T10:00:00+08:00"',
    'updated: "2026-10-30T10:00:00+08:00"', 'description: \'技术 & 实践 <script>\'',
    'tags: ["测试"]', 'sticky: false', '---', '', '# 文章 & 笔记', '',
    '## 中文 章节', '', '**正文**、[下一篇](./未记录.md?q=1#中文)、![示意](./配图.png)。', '',
    '| 项 | 值 |', '| --- | --- |', '| 笔记 | 一 |', '',
    '```js', 'const message = "<script>";', '```', '',
    '<script>alert(1)</script>', '<img src="x.png" onerror="alert(2)">', '', '[危险](javascript:alert%283%29)',
    '', '## 中文 章节', '',
  ].join('\n'));
  fs.writeFileSync(path.join(contentDir, 'blog', '未记录.md'), '# 未记录');
  fs.writeFileSync(path.join(contentDir, 'blog', '旧文.md'), '---\ndate: "2026-09-29T10:00:00+08:00"\n---\n# 旧文');
  fs.mkdirSync(path.join(contentDir, 'knowledge'));
  fs.writeFileSync(path.join(contentDir, 'knowledge', '知识.md'), '---\ndate: "2026-10-29T10:00:00+08:00"\n---\n# 知识');
  const manifest = build({ contentDir, outDir: path.join(root, 'generated') });
  return { manifest, outDir, read: name => fs.readFileSync(path.join(outDir, name), 'utf8') };
}

test('文章入口无脚本也有格式化正文，链接采用部署前缀，危险内容不会进入页面', async (t) => {
  const { manifest, outDir, read } = fixture(t);
  const { writePublicPages } = await import('./publicPages.mjs');
  writePublicPages({
    manifest, outDir, base: '/repo/', siteUrl: 'https://example.com',
    assets: { 'blog/配图.png': '/repo/assets/picture.png' },
  });

  const html = read('blog/文章 #1/index.html');
  assert.match(html, /<div id="app">\s*<main/);
  assert.match(html, /<strong>正文<\/strong>/);
  assert.match(html, /<table>[\s\S]*<td>笔记<\/td>/);
  assert.match(html, /<pre><code class="language-js">/);
  assert.match(html, /<h2 id="中文-章节">中文 章节<\/h2>/);
  assert.match(html, /<h2 id="中文-章节-1">/);
  assert.equal(html.match(/<h1>/g)?.length, 1);
  assert.match(html, /href="\/repo\/blog\/%E6%9C%AA%E8%AE%B0%E5%BD%95\?q=1#%E4%B8%AD%E6%96%87"/);
  assert.match(html, /src="\/repo\/assets\/picture.png"/);
  assert.doesNotMatch(html, /alert\(1\)|onerror=|href="javascript:/);
  assert.match(html, /<script type="module" src="\/repo\/assets\/app.js"/);
  assert.match(read('blog/index.html'), /博客介绍/);
  assert.doesNotMatch(read('blog/index.html'), /首页同名文章/);
});

test('公开域名生成转义后的页面元信息、站点地图与仅含有效日期博客的 RSS', async (t) => {
  const { manifest, outDir, read } = fixture(t);
  const { writePublicPages } = await import('./publicPages.mjs');
  writePublicPages({ manifest, outDir, base: '/repo/', siteUrl: 'https://example.com' });

  const html = read('blog/文章 #1/index.html');
  const url = 'https://example.com/repo/blog/%E6%96%87%E7%AB%A0%20%231/';
  assert.ok(html.includes(`<link rel="canonical" href="${url}">`));
  assert.ok(html.includes(`<meta property="og:url" content="${url}">`));
  assert.match(html, /<title>文章 &amp; 笔记 - 箓川码笺<\/title>/);
  assert.match(html, /<meta name="description" content="技术 &amp; 实践 &lt;script&gt;">/);
  assert.match(html, /type="application\/rss\+xml"[^>]*href="https:\/\/example.com\/repo\/rss.xml"/);

  const sitemap = read('sitemap.xml');
  assert.ok(sitemap.includes(`<loc>${url}</loc><lastmod>2026-10-30T02:00:00.000Z</lastmod>`));
  assert.match(sitemap, /<loc>https:\/\/example.com\/repo\/knowledge\//);
  const feed = read('rss.xml');
  assert.ok(feed.includes(`<guid>${url}</guid>`));
  assert.ok(feed.indexOf('文章 &amp; 笔记') < feed.indexOf('旧文'));
  assert.match(feed, /Thu, 29 Oct 2026 02:00:00 GMT/);
  assert.doesNotMatch(feed, /未记录|<title>知识<\/title>|<title>博客介绍<\/title>/);
});

test('无 SITE_URL 时仍输出根路径正文，无效的公开 origin 会报错', async (t) => {
  const { manifest, outDir, read } = fixture(t);
  const { writePublicPages } = await import('./publicPages.mjs');
  assert.throws(() => writePublicPages({ manifest, outDir, base: '/', siteUrl: 'https://example.com/repo/' }), /SITE_URL/);
  writePublicPages({ manifest, outDir, base: '/' });
  const html = read('blog/文章 #1/index.html');
  assert.match(html, /<strong>正文<\/strong>/);
  assert.doesNotMatch(html, /rel="canonical"|og:url|rss\.xml/);
  assert.equal(fs.existsSync(path.join(outDir, 'sitemap.xml')), false);
  assert.equal(fs.existsSync(path.join(outDir, 'rss.xml')), false);
});
