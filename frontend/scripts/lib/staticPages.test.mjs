import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { writeStaticPages } from './staticPages.mjs';

test('为文章、分类与工具页生成可直接访问的静态入口，保留构建 base', (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-routes-'));
  t.after(() => fs.rmSync(outDir, { recursive: true, force: true }));
  const html = '<html><script src="/repo/assets/app.js"></script></html>';
  fs.writeFileSync(path.join(outDir, 'index.html'), html);
  writeStaticPages({ outDir, manifest: {
    tree: [{ name: 'knowledge', path: '/knowledge', children: [
      { name: '中文目录', path: '/knowledge/中文目录', children: [
        { name: '笔记 #1.md', path: '/knowledge/中文目录/笔记 #1', article: {}, children: [] },
      ] },
    ] }],
    tags: { 'C++ 入门': ['/knowledge/中文目录/笔记 #1'] },
  } });
  for (const route of ['', 'knowledge', 'knowledge/中文目录', 'knowledge/中文目录/笔记 #1', 'about', 'archive', 'tags', 'tags/C++ 入门']) {
    assert.equal(fs.readFileSync(path.join(outDir, route, 'index.html'), 'utf8'), html, route);
  }
  assert.equal(fs.readFileSync(path.join(outDir, '404.html'), 'utf8'), html);
  assert.ok(fs.existsSync(path.join(outDir, '.nojekyll')));
  assert.equal(fs.existsSync(path.join(outDir, 'knowledge/中文目录/README/index.html')), false);
});

test('内容栏目占用 tags/archive 时不额外生成标签工具路由', (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-custom-sections-'));
  t.after(() => fs.rmSync(outDir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(outDir, 'index.html'), '<html></html>');
  writeStaticPages({ outDir, manifest: {
    tree: ['tags', 'archive'].map(name => ({ name, path: '/' + name, children: [] })),
    tags: { hiddenToolRoute: ['/knowledge/test'] },
  } });
  assert.ok(fs.existsSync(path.join(outDir, 'tags/index.html')));
  assert.ok(fs.existsSync(path.join(outDir, 'archive/index.html')));
  assert.equal(fs.existsSync(path.join(outDir, 'tags/hiddenToolRoute/index.html')), false);
});

test('拒绝输出到构建目录之外的页面路径', (t) => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-safe-paths-'));
  t.after(() => fs.rmSync(outDir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(outDir, 'index.html'), '<html></html>');
  assert.throws(() => writeStaticPages({ outDir, manifest: {
    tree: [{ name: 'bad', path: '/../outside', children: [] }], tags: {},
  } }), /构建目录/);
});
