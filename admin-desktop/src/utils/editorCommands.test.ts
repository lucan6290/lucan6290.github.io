// @ts-nocheck -- Node 测试通过脚本转译运行，不进入浏览器。
import assert from 'node:assert/strict'
import test from 'node:test'
import { applyMarkdownCommand } from './editorCommands'

test('格式化所选文本并保留其他行与可继续编辑的选区', () => {
  assert.deepEqual(applyMarkdownCommand('甲例子乙', 1, 3, 'bold'), {
    text: '甲**例子**乙', start: 3, end: 5,
  })
  assert.deepEqual(applyMarkdownCommand('a\n正文\nb', 3, 4, 'heading'), {
    text: 'a\n## 正文\nb', start: 5, end: 7,
  })
})

test('链接操作选中目标占位地址并保留文字', () => {
  const result = applyMarkdownCommand('示例', 0, 2, 'link')
  assert.equal(result.text, '[示例](https://)')
  assert.equal(result.text.slice(result.start, result.end), 'https://')
})
