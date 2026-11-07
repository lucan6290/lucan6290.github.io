import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { build } from './buildContent.mjs';
import { createSearch } from '../../src/composables/search.ts';
import { contentHref } from '../../src/composables/contentPaths.ts';

test('全文索引覆盖摘要后的正文及代码，排除隐藏文档和分类介绍，并随重建更新', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'reader-search-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const category = path.join(contentDir, 'knowledge', '中文目录');
  fs.mkdirSync(category, { recursive: true });
  const article = path.join(category, '配置 #1.md');
  fs.writeFileSync(article, '---\ntitle: 安装笔记\ndescription: 简短摘要\nsecret: 不索引的元数据\n---\n' + '开头文字。'.repeat(60) + '\n环境变量配置\n```ts\nconst uniqueCodeToken = 1;\n```\n![配图](./private-image.png)\n[文档](https://private-url.invalid)');
  fs.writeFileSync(path.join(category, 'README.md'), '# 分类介绍');
  fs.writeFileSync(path.join(category, '_草稿.md'), '# 私有草稿');
  fs.writeFileSync(path.join(contentDir, 'about.md'), '# 根级占位文档');
  const options = { contentDir, outDir: path.join(root, 'generated') };
  const { searchDocs } = build(options);
  assert.equal(searchDocs.length, 1);
  assert.match(searchDocs[0].body, /环境变量配置/);
  assert.match(searchDocs[0].body, /uniqueCodeToken/);
  assert.doesNotMatch(searchDocs[0].body, /不索引的元数据|private-image|private-url/);
  assert.deepEqual(createSearch(searchDocs)('变量配置').map(result => result.path), ['/knowledge/中文目录/配置 #1']);
  assert.equal(contentHref(searchDocs[0].path), '/knowledge/%E4%B8%AD%E6%96%87%E7%9B%AE%E5%BD%95/%E9%85%8D%E7%BD%AE%20%231');
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(options.outDir, 'search-index.json'), 'utf8')), searchDocs);
  fs.writeFileSync(article, '# 替换标题\n\n新的检索关键词');
  const updated = createSearch(build(options).searchDocs);
  assert.equal(updated('uniqueCodeToken').length, 0);
  assert.equal(updated('检索关键词').length, 1);
  fs.unlinkSync(article);
  assert.deepEqual(build(options).searchDocs, []);
});

const documents = [
  { id: 'body', path: '/blog/body', title: '开发笔记', description: '', tags: '', body: '环境变量配置 VueRouter 技术文档' },
  { id: 'title', path: '/knowledge/title', title: '环境变量配置', description: '', tags: '', body: '安装说明' },
  { id: 'tags', path: '/projects/tags', title: '工具', description: '自动生成摘要', tags: 'TypeScript', body: '' },
  { id: 'unrelated', path: '/blog/unrelated', title: '日记', description: '', tags: '', body: '环境很好，变量很多，配置另说' },
];

test('中文连续短语可匹配正文，标题优先，多词采用 AND', () => {
  const search = createSearch(documents);
  assert.deepEqual(search('变量配置').map(result => result.id), ['title', 'body']);
  assert.deepEqual(search('环境 VueRou').map(result => result.id), ['body']);
  assert.equal(search('环境 不存在').length, 0);
});

test('英文大小写、前缀、标签、摘要和中英文混排可检索', () => {
  const search = createSearch(documents);
  assert.deepEqual(search('vUeRo').map(result => result.id), ['body']);
  assert.deepEqual(search('环境VueRouter').map(result => result.id), ['body']);
  assert.deepEqual(search('typescript').map(result => result.id), ['tags']);
  assert.deepEqual(search('自动生成').map(result => result.id), ['tags']);
  assert.equal(search('量').length, 3);
});

test('空白、纯标点及无结果查询返回空数组，空索引可查询', () => {
  const search = createSearch(documents);
  for (const query of ['', '  \n ', '！？---', 'doesnotexist']) assert.deepEqual(search(query), []);
  assert.deepEqual(createSearch([])('配置'), []);
});

test('大量结果限制为 30 条且不回传正文', () => {
  const search = createSearch(Array.from({ length: 40 }, (_, index) => ({
    id: String(index), path: `/blog/${index}`, title: '搜索测试', description: '摘要', tags: '', body: '正文',
  })));
  const results = search('搜索');
  assert.equal(results.length, 30);
  assert.equal(results[0].description, '摘要');
  assert.equal('body' in results[0], false);
});

test('搜索保留泛型、比较表达式及行内代码的关键词，摘要排除注释和图片地址', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'search-code-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'knowledge'), { recursive: true });
  fs.writeFileSync(path.join(contentDir, 'knowledge', '代码.md'), [
    '<!-- hiddenOnlyKeyword -->',
    '![图示](./privateImageKeyword.png)',
    '# 代码检索',
    '`Array<InlineGenericKeyword>`',
    '```ts',
    'const value: Array<FencedGenericKeyword> = [];',
    'if (left < right) {',
    '  comparisonKeyword();',
    '}',
    'if (count > 0) {}',
    '```',
    '~~~ts',
    'const value: Array<TildeGenericKeyword> = [];',
    '~~~',
  ].join('\n'));
  const { searchDocs } = build({ contentDir, outDir: path.join(root, 'generated') });
  const search = createSearch(searchDocs);
  for (const keyword of ['InlineGenericKeyword', 'FencedGenericKeyword', 'comparisonKeyword', 'TildeGenericKeyword']) {
    assert.equal(search(keyword).length, 1, `${keyword} 应保留在代码中`);
  }
  for (const keyword of ['hiddenOnlyKeyword', 'privateImageKeyword']) {
    assert.deepEqual(search(keyword), [], `${keyword} 不应经摘要进入索引`);
    assert.doesNotMatch(searchDocs[0].description, new RegExp(keyword));
  }
});
