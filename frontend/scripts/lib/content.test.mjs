import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { build } from './buildContent.mjs';
import { createNavEntries } from '../../src/config/nav.ts';

test('一级空目录成为栏目，隐藏和资源目录不成为栏目', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-sections-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  for (const name of ['knowledge', 'blog', 'projects', 'about', '学习路线', '.hidden', '_草稿', 'images', 'assets', '配图-imgs']) {
    fs.mkdirSync(path.join(contentDir, name), { recursive: true });
  }
  fs.mkdirSync(path.join(contentDir, 'knowledge', '空子目录'));
  const options = { contentDir, outDir: path.join(root, 'generated') };
  const result = build(options);
  assert.deepEqual(result.tree.map(n => n.name).sort(), ['about', 'blog', 'knowledge', 'projects', '学习路线'].sort());
  assert.deepEqual(result.tree.find(n => n.name === 'knowledge').children.map(n => n.name), ['空子目录']);
  fs.rmdirSync(path.join(contentDir, '学习路线'));
  assert.equal(build(options).tree.some(n => n.name === '学习路线'), false);
});

test('知识库保留两级空分类，下拉只列一级文件夹，文档保留在二级分类', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'knowledge-levels-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const category = path.join(contentDir, 'knowledge', 'Java', '集合框架');
  fs.mkdirSync(category, { recursive: true });
  fs.mkdirSync(path.join(contentDir, 'knowledge', 'images'));
  fs.mkdirSync(path.join(contentDir, 'knowledge', '_草稿'));
  fs.writeFileSync(path.join(contentDir, 'knowledge', '说明.md'), '# 说明');
  const options = { contentDir, outDir: path.join(root, 'generated') };
  let result = build(options);
  const java = result.tree.find(n => n.name === 'knowledge').children.find(n => n.name === 'Java');
  assert.ok(java, '空的一级分类仍保留');
  assert.equal(java.children[0].path, '/knowledge/Java/集合框架');
  assert.deepEqual(createNavEntries(result.tree)[0].items.map(n => n.label), ['首页', 'Java']);
  fs.writeFileSync(path.join(category, 'HashMap.md'), '# HashMap 笔记\n\n正文');
  result = build(options);
  assert.ok(result.articles['/knowledge/Java/集合框架/HashMap']);
  assert.deepEqual(createNavEntries(result.tree)[0].items.map(n => n.label), ['首页', 'Java']);
  fs.unlinkSync(path.join(category, 'HashMap.md'));
  assert.equal(build(options).tree[0].children.find(n => n.name === 'Java').children[0].children.length, 0);
  fs.rmdirSync(category);
  fs.rmdirSync(path.dirname(category));
  assert.deepEqual(createNavEntries(build(options).tree)[0].items.map(n => n.label), ['首页']);
});

for (const section of ['projects', 'blog']) test(`${section} 目录保留空分类并自动收录子目录中的 Markdown`, (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'projects-levels-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const category = path.join(contentDir, section, '01-我的项目');
  const nested = path.join(category, '桌面工具');
  fs.mkdirSync(nested, { recursive: true });
  const options = { contentDir, outDir: path.join(root, 'generated') };
  let result = build(options);
  const project = result.tree.find(node => node.name === section);
  assert.ok(project.children.find(node => node.name === '01-我的项目'), '空分类仍保留');
  assert.equal(project.children[0].children[0].path, `/${section}/01-我的项目/桌面工具`);
  fs.writeFileSync(path.join(nested, 'TerminalVoice.md'), '# TerminalVoice\n\n语音工具');
  result = build(options);
  assert.equal(result.articles[`/${section}/01-我的项目/桌面工具/TerminalVoice`].frontmatter.title, 'TerminalVoice');
  assert.deepEqual(createNavEntries(result.tree)[0].items.slice(1).map(item => item.label), ['我的项目']);
});

test('复制笔记文件夹后生成标题、分类介绍，过滤资源目录', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-content-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  const write = (name, text) => {
    const file = path.join(contentDir, name);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, text);
  };
  write('knowledge/Python/README.md', '# Python 入门\n\n分类介绍');
  write('knowledge/Python/01-安装.md', '# 安装环境\n\n正文');
  write('knowledge/Python/02-语法.md', '---\ntitle: 自定义标题\n---\n# 语法');
  write('knowledge/Python/03-无标题.md', '只有正文');
  write('knowledge/Python/04-代码示例.md', '```md\n# 代码里的标题\n```\n# 真正标题');
  write('knowledge/Python/05-Csharp.md', '# C#');
  write('knowledge/Python/images/说明.md', '# 资源目录内说明，不是笔记');
  write('knowledge/Python/配图-imgs/a.png', 'image');
  write('knowledge/Python/仅图片/a.png', 'image');
  write('knowledge/Python/介绍/readme.md', '# 只有介绍的分类');
  write('knowledge/Python/_草稿.md', '# 不发布');
  write('blog/随笔/随笔.md', '# 同名文件夹中的文章');

  const result = build({ contentDir, outDir: path.join(root, 'generated') });
  assert.equal(result.articles['/knowledge/Python/01-安装'].frontmatter.title, '安装环境');
  assert.equal(result.articles['/knowledge/Python/02-语法'].frontmatter.title, '自定义标题');
  assert.equal(result.articles['/knowledge/Python/03-无标题'].frontmatter.title, '无标题');
  assert.equal(result.articles['/knowledge/Python/04-代码示例'].frontmatter.title, '真正标题');
  assert.equal(result.articles['/knowledge/Python/05-Csharp'].frontmatter.title, 'C#');
  assert.ok(result.articles['/blog/随笔/随笔']);
  const category = result.tree.find(n => n.name === 'knowledge').children[0];
  assert.equal(category.introduction.rawContent, '# Python 入门\n\n分类介绍');
  assert.equal(category.introduction.relativePath, 'knowledge/Python/README.md');
  assert.deepEqual(category.children.map(n => n.name), ['介绍', '01-安装.md', '02-语法.md', '03-无标题.md', '04-代码示例.md', '05-Csharp.md']);
  assert.equal(Object.keys(result.articles).length, 6);
});

test('文章字数统计排除 Markdown 标记、图片和代码块', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-word-count-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const file = path.join(root, 'content', 'blog', '统计.md');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `---\ntitle: 统计练习\n---\n# 中文标题\n\n正文包含 CSDN 和 TypeScript，**重点**、\`命令\`，并有[链接文字](https://example.com)。\n\n![图片](./image.png)\n\n\`\`\`ts\nconst hiddenText = '不计入统计';\n\`\`\`\n`);

  const result = build({ contentDir: path.join(root, 'content'), outDir: path.join(root, 'generated') });
  assert.equal(result.articles['/blog/统计'].wordCount, 21);
});

test('阅读时长按每分钟 300 字向上取整，空文和短文至少 1 分钟', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-reading-time-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'blog'), { recursive: true });
  for (const count of [0, 1, 300, 301, 2164]) {
    fs.writeFileSync(path.join(contentDir, 'blog', `${count}.md`), '字'.repeat(count));
  }
  const { articles } = build({ contentDir, outDir: path.join(root, 'generated') });
  for (const [count, minutes] of [[0, 1], [1, 1], [300, 1], [301, 2], [2164, 8]]) {
    assert.equal(articles[`/blog/${count}`].wordCount, count);
    assert.equal(articles[`/blog/${count}`].readingMinutes, minutes);
  }
});

test('字数和阅读时长不计入波浪号、长反引号围栏和 HTML 注释', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-reading-code-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'knowledge'), { recursive: true });
  const hidden = '不计入统计'.repeat(100);
  fs.writeFileSync(path.join(contentDir, 'knowledge', '围栏.md'), [
    '正文 Vue 3', '~~~js', hidden, '~~~', '````md', '```', hidden, '```', '````', `<!-- ${hidden} -->`,
  ].join('\n'));
  const article = build({ contentDir, outDir: path.join(root, 'generated') }).articles['/knowledge/围栏'];
  assert.equal(article.wordCount, 4);
  assert.equal(article.readingMinutes, 1);
});

for (const [name, body, wordCount, readingMinutes] of [
  ['代码中的注释起始符不会吞掉后续正文', ['```html', '<!--', '```', '字'.repeat(301)].join('\n'), 301, 2],
  ['引用内的围栏代码不计入字数', ['> ```js', '> ' + '字'.repeat(301), '> ```', '', '正文'].join('\n'), 2, 1],
  ['注释内的围栏不会隐藏注释后的正文', ['<!--', '```', '隐藏内容', '-->', '', '字'.repeat(301)].join('\n'), 301, 2],
]) test(name, (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-markdown-stats-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'blog'), { recursive: true });
  fs.writeFileSync(path.join(contentDir, 'blog', '统计.md'), body);
  const article = build({ contentDir, outDir: path.join(root, 'generated') }).articles['/blog/统计'];
  assert.equal(article.wordCount, wordCount);
  assert.equal(article.readingMinutes, readingMinutes);
});

test('日期仅来自 YAML，缺失或无效日期不回退为文件时间', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-article-dates-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'projects'), { recursive: true });
  const cases = [
    ['未填写', '', '', ''],
    ['无效', 'date: "不是日期"\nupdated: "未知"', '', ''],
    ['仅创建', 'date: "2026-10-01T09:00:00+08:00"', '2026-10-01T09:00:00+08:00', ''],
    ['仅更新', 'updated: "2026-10-02T11:30:00+08:00"', '', '2026-10-02T11:30:00+08:00'],
    ['相同', 'date: "2026-10-01T09:00:00+08:00"\nupdated: "2026-10-01T09:00:00+08:00"', '2026-10-01T09:00:00+08:00', '2026-10-01T09:00:00+08:00'],
    ['同日更新', 'date: "2026-10-01T09:00:00+08:00"\nupdated: "2026-10-01T11:30:00+08:00"', '2026-10-01T09:00:00+08:00', '2026-10-01T11:30:00+08:00'],
    ['YAML日期', 'date: 2026-10-01T09:00:00+08:00\nupdated: 2026-10-02T11:30:00+08:00', '2026-10-01T01:00:00.000Z', '2026-10-02T03:30:00.000Z'],
  ];
  for (const [name, yaml] of cases) {
    const file = path.join(contentDir, 'projects', `${name}.md`);
    fs.writeFileSync(file, `---\n${yaml}\n---\n# ${name}\n正文`);
    fs.utimesSync(file, new Date('2030-01-01T00:00:00Z'), new Date('2030-01-01T00:00:00Z'));
  }
  const result = build({ contentDir, outDir: path.join(root, 'generated') });
  for (const [name, , date, updated] of cases) {
    assert.equal(result.articles[`/projects/${name}`].frontmatter.date, date, name);
    assert.equal(result.articles[`/projects/${name}`].frontmatter.updated, updated, name);
  }
  assert.deepEqual(Object.keys(result.archive), ['2026']);
  assert.equal(Object.values(result.archive['2026']).flat().length, 4);
});

test('最近文章按真实更新时间排序，无日期文章排在末尾', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'notes-recent-dates-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const contentDir = path.join(root, 'content');
  fs.mkdirSync(path.join(contentDir, 'blog'), { recursive: true });
  for (const [name, yaml] of [
    ['a-未填写', ''],
    ['b-较早', 'date: "2026-10-01T10:00:00+08:00"'],
    ['c-较晚', 'date: "2026-10-02T10:00:00+08:00"'],
    ['d-更新', 'date: "2026-09-01T10:00:00+08:00"\nupdated: "2026-10-03T10:00:00+08:00"'],
  ]) {
    fs.writeFileSync(path.join(contentDir, 'blog', `${name}.md`), `---\n${yaml}\n---\n正文`);
  }
  const { recent } = build({ contentDir, outDir: path.join(root, 'generated') });
  assert.deepEqual(recent, ['/blog/d-更新', '/blog/c-较晚', '/blog/b-较早', '/blog/a-未填写']);
});
