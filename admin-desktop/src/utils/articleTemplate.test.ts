// @ts-nocheck -- Executed by Node after TypeScript transpilation, outside the browser build.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createArticleTemplate, formatBeijingTime, fillArticleTitle, isArticleDocument } from './articleTemplate'

test('开始写作时间用北京时间秒级格式，跨日不依赖机器时区', () => {
  assert.equal(formatBeijingTime(new Date('2026-10-29T18:04:05Z')), '2026-10-30T02:04:05+08:00')
})

test('模板六字段固定顺序，空标题摘要可编辑、无假标签，初始日期相同', () => {
  assert.equal(createArticleTemplate(new Date('2026-10-29T02:04:05Z')), '---\ntitle: ""\ndate: "2026-10-29T10:04:05+08:00"\nupdated: "2026-10-29T10:04:05+08:00"\ndescription: ""\ntags: []\nsticky: false\n---\n\n# \n')
})

test('文件名回填空标题与空H1，去编号且转义双引号和反斜杠', () => {
  const raw = '---\ntitle: ""\ndescription: ""\n---\n\n# \n正文\n'
  assert.equal(fillArticleTitle(raw, '01-引号"与反斜杠\\.md'), '---\ntitle: "引号\\\"与反斜杠\\\\"\ndescription: ""\n---\n\n# 引号"与反斜杠\\\n正文\n')
})

test('文件名不覆盖作者填写的标题或正文H1', () => {
  const authored = '---\ntitle: "作者标题"\n---\n\n# 作者标题\n'
  assert.equal(fillArticleTitle(authored, '02-文件名.md'), authored)
  const heading = '---\ntitle: ""\n---\n\n# 已填写正文标题\n'
  assert.equal(fillArticleTitle(heading, '02-文件名.md'), heading)
})

test('README与AGENTS不分大小写豁免，其他说明由用户显式选择', () => {
  assert.equal(isArticleDocument('blog/rEaDmE.mD', true), false)
  assert.equal(isArticleDocument('AGENTS.md', true), false)
  assert.equal(isArticleDocument('blog/设计说明.md', true), true)
  assert.equal(isArticleDocument('blog/设计说明.md', false), false)
})
