import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { build } from './buildContent.mjs';

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
  assert.deepEqual(result.tree.find(n => n.name === 'knowledge').children, []);
  fs.rmdirSync(path.join(contentDir, '学习路线'));
  assert.equal(build(options).tree.some(n => n.name === '学习路线'), false);
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
