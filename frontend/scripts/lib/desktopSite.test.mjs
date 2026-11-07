import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import { sitePreviewRoute } from '../../src/vite/desktopSitePlugin.ts';

test('桌面预览按真实文档路径打开文章、README 和首页', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'luchuan-preview-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const path of ['README.md', 'blog/二 级/01-100% #内容.MDX', 'blog/二 级/readme.MD', 'blog/_draft.md']) {
    const parts = path.split('/');
    mkdirSync(join(root, ...parts.slice(0, -1)), { recursive: true });
    writeFileSync(join(root, ...parts), '# 内容');
  }

  assert.equal(sitePreviewRoute(root, null), '/');
  assert.equal(sitePreviewRoute(root, 'README.md'), '/');
  assert.equal(sitePreviewRoute(root, 'blog/二 级/01-100% #内容.MDX'), '/blog/%E4%BA%8C%20%E7%BA%A7/01-100%25%20%23%E5%86%85%E5%AE%B9');
  assert.equal(sitePreviewRoute(root, 'blog/二 级/readme.MD'), '/blog/%E4%BA%8C%20%E7%BA%A7');
  assert.equal(sitePreviewRoute(root, 'blog/_draft.md'), null);
  assert.equal(sitePreviewRoute(root, 'blog/../../README.md'), null);
  assert.equal(sitePreviewRoute(root, 'blog/不存在.md'), null);
});
