import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { build } from './buildContent.mjs';
import { writePublicPages } from './publicPages.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'content-series-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const outDir = path.join(root, 'generated');
  const dist = path.join(root, 'dist');
  fs.mkdirSync(dist);
  fs.writeFileSync(path.join(dist, 'index.html'), '<html><head><title>箓川码笺</title></head><body><div id="app"></div></body></html>');
  return {
    dist,
    build: () => build({ contentDir, outDir }),
    read: file => fs.readFileSync(path.join(dist, file), 'utf8'),
    write(file, title, series) {
      const target = path.join(contentDir, file);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      const optional = series ? '\nseries: ' + JSON.stringify(series) : '';
      fs.writeFileSync(target, `---\ntitle: "${title}"\ndate: "2026-10-29T10:00:00+08:00"\nupdated: "2026-10-29T10:00:00+08:00"\ndescription: "系列文章"\ntags: []\nsticky: false${optional}\n---\n\n# ${title}\n\n文章正文。`);
    },
  };
}

test('系列横跨目录且按显式次序排列，文章地址和直属目录前后篇保持不变', (t) => {
  const files = fixture(t);
  files.write('blog/01-先扫描.md', '第二部分', { id: 'learning', title: '学习 & 实践', order: 20 });
  files.write('blog/02-普通文章.md', '普通文章');
  files.write('blog/README.md', '目录介绍', { id: 'learning', title: '学习 & 实践', order: 20 });
  files.write('knowledge/中文目录/学习 笔记.md', '第一部分', { id: 'learning', title: '学习 & 实践', order: 10 });
  const manifest = files.build();
  assert.deepEqual(manifest.series.learning, {
    id: 'learning', title: '学习 & 实践', articlePaths: ['/knowledge/中文目录/学习 笔记', '/blog/01-先扫描'],
  });
  assert.equal(manifest.articles['/blog/02-普通文章'].frontmatter.series, undefined);
  assert.equal(manifest.prevNext['/blog/01-先扫描'].next.path, '/blog/02-普通文章');

  writePublicPages({ manifest, outDir: files.dist, base: '/repo/', siteUrl: 'https://example.com' });
  const listing = files.read('series/learning/index.html');
  assert.match(listing, /<h1>学习 &amp; 实践<\/h1>/);
  assert.match(listing, /<ol>[\s\S]*第一部分[\s\S]*第二部分[\s\S]*<\/ol>/);
  assert.match(listing, /href="\/repo\/knowledge\/%E4%B8%AD%E6%96%87%E7%9B%AE%E5%BD%95\/%E5%AD%A6%E4%B9%A0%20%E7%AC%94%E8%AE%B0\/"/);
  assert.match(files.read('series/index.html'), /href="\/repo\/series\/learning\/"/);
  assert.match(files.read('blog/01-先扫描/index.html'), /href="\/repo\/series\/learning\/"/);
  assert.doesNotMatch(files.read('blog/02-普通文章/index.html'), /series\/learning/);
  assert.match(files.read('sitemap.xml'), /<loc>https:\/\/example.com\/repo\/series\/learning\/<\/loc>/);
});

test('系列 YAML 错误能定位到源文件，重复顺序和同一 ID 的标题冲突会报错', (t) => {
  const files = fixture(t);
  const member = { id: 'learning', title: '学习', order: 1 };
  files.write('blog/01-甲.md', '甲', member);
  files.write('blog/02-乙.md', '乙', { ...member, order: '2' });
  assert.throws(files.build, /02-乙\.md.*series\.order/);
  files.write('blog/02-乙.md', '乙', { ...member, id: '../outside' });
  assert.throws(files.build, /02-乙\.md.*series\.id/);
  files.write('blog/02-乙.md', '乙', member);
  assert.throws(files.build, /02-乙\.md.*series\.order.*重复/);
  files.write('blog/02-乙.md', '乙', { ...member, title: '不同标题', order: 2 });
  assert.throws(files.build, /02-乙\.md.*series\.title.*不一致/);
});

test('无系列时可生成空状态，已有同名栏目保持原内容路由', (t) => {
  const files = fixture(t);
  const options = { outDir: files.dist, base: '/', siteUrl: 'https://example.com' };
  writePublicPages({ ...options, manifest: files.build() });
  assert.match(files.read('series/index.html'), /暂无系列专题/);
  // 重新构建时 Vite 会创建新的模板。
  fs.writeFileSync(path.join(files.dist, 'index.html'), '<html><head></head><body><div id="app"></div></body></html>');
  files.write('series/目录正文.md', '同名栏目原内容');
  const manifest = files.build();
  writePublicPages({ ...options, manifest });
  assert.match(files.read('series/index.html'), /同名栏目原内容/);
  files.write('blog/系列成员.md', '成员', { id: 'learning', title: '学习', order: 1 });
  assert.throws(files.build, /content\/series.*占用/);
});
