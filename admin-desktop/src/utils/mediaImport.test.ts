// @ts-nocheck -- Node 测试通过脚本转译运行，不进入浏览器。
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { insertImageReferences } from './mediaImport'

test('图片引用插在当前行之后，保留用户写作内容并定位下一个空行', () => {
  assert.deepEqual(insertImageReferences('原文后半\n下一行', 2, ['![图](./图.png)', '![图二](./二.png)']), {
    text: '原文后半\n\n![图](./图.png)\n\n![图二](./二.png)\n\n下一行',
    caret: '原文后半\n\n![图](./图.png)\n\n![图二](./二.png)\n\n'.length,
  })
  assert.deepEqual(insertImageReferences('', 0, ['![图](./图.png)']), {
    text: '![图](./图.png)\n\n',
    caret: '![图](./图.png)\n\n'.length,
  })
})


test('在 YAML 中触发导入时将引用放到正文，保留头部和后续文本', () => {
  const original = '---\ntitle: "文章"\n---\n\n正文'
  assert.equal(insertImageReferences(original, 1, ['![图](./图.png)']).text,
    '---\ntitle: "文章"\n---\n\n![图](./图.png)\n\n\n正文')
})
