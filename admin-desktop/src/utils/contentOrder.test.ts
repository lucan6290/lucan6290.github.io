// @ts-nocheck -- Node 测试通过脚本转译运行，不进入浏览器。
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { compareContentPaths } from './contentOrder'

test('同层编号按数值顺序，未编号目录采用前台相同的本机名称比较', () => {
  const names = ['目录/10-十.md', '目录/2-二.md', '目录/01-一.md', '目录/乙.md', '目录/甲.md', '目录/alpha.md']
  const unnumbered = ['乙.md', '甲.md', 'alpha.md'].sort((a, b) => a.localeCompare(b))
  assert.deepEqual(names.sort(compareContentPaths), ['目录/01-一.md', '目录/2-二.md', '目录/10-十.md', ...unnumbered.map(name => `目录/${name}`)])
})

test('逐段比较目录而非全路径字符串，父目录排列在子目录之前', () => {
  assert.deepEqual(['10-章/01-甲', '2-章/乙', '2-章', '2-章/01-甲'].sort(compareContentPaths), ['2-章', '2-章/01-甲', '2-章/乙', '10-章/01-甲'])
})
