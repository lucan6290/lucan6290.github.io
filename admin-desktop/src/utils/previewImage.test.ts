// @ts-nocheck -- Node 测试通过脚本转译运行，不进入浏览器。
import assert from 'node:assert/strict'
import test from 'node:test'
import { previewImagePath } from './previewImage'

test('预览按文章所在目录解析中文、空格和上级目录', () => {
  const directory = 'blog/分类'
  assert.equal(previewImagePath('./01-文章-images/图%20一.png#demo', directory), 'blog/分类/01-文章-images/图 一.png')
  assert.equal(previewImagePath('../assets/图.png', directory), 'blog/assets/图.png')
})

test('相对图片不允许跳出内容库或借转义插入路径分隔符', () => {
  const directory = 'blog'
  for (const url of ['../../secret.png', 'a%2Fb.png', 'a%5Cb.png', '%FF', '//example.org/img.png', 'https://example.org/img.png']) {
    assert.equal(previewImagePath(url, directory), null)
  }
})
