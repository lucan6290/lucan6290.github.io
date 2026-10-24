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
