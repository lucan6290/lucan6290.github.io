import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createMemoryHistory, createRouter } from 'vue-router';
import { CONTENT_ROUTE_PATH, contentHref, contentPath, resolveContentUrl, sidebarNodes } from '../../src/composables/contentPaths.ts';
import { createNavEntries } from '../../src/config/nav.ts';

test('知识库分类与文章侧栏只展示所属一级目录，其他栏目维持原样', () => {
  const tree = [
    { name: 'project-practice', path: '/knowledge/project-practice', children: [] },
    { name: 'tech-study', path: '/knowledge/tech-study', children: [] },
  ];
  assert.deepEqual(sidebarNodes(tree, '/knowledge', '/knowledge/tech-study'), [tree[1]]);
  assert.deepEqual(sidebarNodes(tree, '/knowledge', '/knowledge/tech-study/子分类/文章'), [tree[1]]);
  assert.deepEqual(sidebarNodes(tree, '/knowledge', '/knowledge/project-practice/文章'), [tree[0]]);
  assert.deepEqual(sidebarNodes(tree, '/blog', '/blog/随笔/文章'), tree);
  assert.deepEqual(sidebarNodes(tree, '/knowledge', '/knowledge/tech-study-more/文章'), []);
});

test('任意栏目路由保留分区前缀与中文目录', () => {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: CONTENT_ROUTE_PATH, component: {} },
  ] });
  for (const input of ['/knowledge', '/knowledge/中文/中文/01-笔记', '/blog/随笔/文章', '/projects', '/about', '/学习 路线/嵌套/第一篇', '/tags/学习/笔记', '/C# 学习/100%笔记']) {
    const route = router.resolve(contentHref(input));
    const root = '/' + route.params.section;
    assert.equal(contentPath(root, route.params.pathMatch), input);
  }
});

test('导航按现有四栏排序，新栏目追加且只有实际子节点', () => {
  const folder = (name, children = []) => ({ name, label: name, path: '/' + name, sortKey: null, children });
  const tree = [folder('学习 路线', [{...folder('01-第一篇.md'), path: '/学习 路线/01-第一篇', label: '第一篇', article: {}}]), folder('about'), folder('blog'), folder('projects'), folder('knowledge'), { ...folder('独立.md'), article: {} }];
  const entries = createNavEntries(tree);
  assert.deepEqual(entries.map(n => n.label), ['知识库', '博客', '项目', '关于', '学习 路线']);
  assert.equal(entries[4].items[0].to, '/' + encodeURIComponent('学习 路线'));
  assert.deepEqual(entries[4].items.map(n => n.label), ['学习 路线首页', '第一篇']);
  assert.deepEqual(entries[0].items, [{ label: '首页', to: '/knowledge' }]);
  assert.equal(createNavEntries(tree.filter(n => n.name !== 'about')).some(n => n.key === 'about'), true);
  assert.equal(tree[0].name, '学习 路线');
});

test('关于是固定入口，不依赖内容目录且没有下拉项', () => {
  const entries = createNavEntries([{ name: 'knowledge', label: 'knowledge', path: '/knowledge', sortKey: null, children: [] }]);
  const about = entries.find(entry => entry.key === 'about');
  assert.deepEqual(about, { key: 'about', label: '关于', rootPath: '/about', items: [] });
});

test('相对文档、README、图片及引用式链接使用源文件位置解析', () => {
  const source = 'knowledge/Python 学习/01-安装.md';
  const resolve = value => resolveContentUrl(value, source, { 'knowledge/Python 学习/images/配置 图.png': '/assets/image-abc.png' });
  assert.equal(resolve('./02-语法.md?mode=read#例子'), '/knowledge/Python%20%E5%AD%A6%E4%B9%A0/02-%E8%AF%AD%E6%B3%95?mode=read#%E4%BE%8B%E5%AD%90');
  assert.equal(resolve('./README.md'), '/knowledge/Python%20%E5%AD%A6%E4%B9%A0');
  assert.equal(resolve('images/配置%20图.png'), '/assets/image-abc.png');
  assert.equal(resolve('../其他/readme.md#简介'), '/knowledge/%E5%85%B6%E4%BB%96#%E7%AE%80%E4%BB%8B');
  for (const value of ['https://example.com/a.md', '//example.com/a.png', '#标题', '/img/favicon.png', 'mailto:a@example.com', '../../../outside.png']) {
    assert.equal(resolve(value), value);
  }
});
