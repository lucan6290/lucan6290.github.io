import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createMemoryHistory, createRouter } from 'vue-router';
import { contentPath, resolveContentUrl } from '../../src/composables/contentPaths.ts';

test('知识库、博客路由保留分区前缀与中文目录', () => {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/knowledge/:pathMatch(.*)*', component: {} },
    { path: '/blog/:pathMatch(.*)*', component: {} },
  ] });
  for (const input of ['/knowledge', '/knowledge/中文/中文/01-笔记', '/blog/随笔/文章']) {
    const route = router.resolve(input);
    const root = input.startsWith('/blog') ? '/blog' : '/knowledge';
    assert.equal(contentPath(root, route.params.pathMatch), input);
  }
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
