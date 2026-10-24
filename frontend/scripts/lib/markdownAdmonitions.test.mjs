import assert from 'node:assert/strict';
import { test } from 'node:test';

test('Docusaurus admonitions become styled Markdown blockquotes without changing fenced code', async () => {
  const { transformDocusaurusAdmonitions } = await import('../../src/utils/markdownAdmonitions.js').catch(() => ({}));
  assert.equal(typeof transformDocusaurusAdmonitions, 'function', 'admonition transformer is available');

  const source = [
    ':::warning',
    '除非是自己一个人开发的仓库，否则不建议这样操作！',
    ':::',
    '',
    ':::tip[自定义提示]',
    '先确认目标分支。',
    ':::',
    '',
    '```md',
    ':::warning',
    '这段是代码示例，不是提示块。',
    ':::',
    '```',
  ].join('\n');

  const rendered = transformDocusaurusAdmonitions(source);
  assert.match(rendered, /> \*\*\[!warning\] 注意\*\*/);
  assert.match(rendered, /> 除非是自己一个人开发的仓库，否则不建议这样操作！/);
  assert.match(rendered, /> \*\*\[!tip\] 自定义提示\*\*/);
  assert.ok(rendered.includes('```md\n:::warning\n这段是代码示例，不是提示块。\n:::\n```'));
});
