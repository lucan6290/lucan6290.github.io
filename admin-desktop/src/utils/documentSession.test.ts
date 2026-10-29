// @ts-nocheck -- Executed by Node after TypeScript transpilation, outside the browser build.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { DocumentSession } from './documentSession'
import { contentApi } from '../api/content'

function detail(raw = '# 原文\n', version = 'v1', path = 'knowledge/文档.md') {
  return { relative_path: path, name: '文档.md', title: '原文', section: 'knowledge', kind: 'article', tags: [], description: '', date: null, updated: null, modified_at: '', version, raw_content: raw, frontmatter: {} }
}
function opened(raw = '# 原文\n') {
  const session = new DocumentSession()
  session.begin('knowledge/文档.md')
  session.load(detail(raw), session.generation)
  return session
}
function deferred() {
  let resolve
  const promise = new Promise(r => { resolve = r })
  return { promise, resolve }
}

test('BOM/CRLF 原文无改动不写盘；修改后只恢复原换行和BOM', async () => {
  const session = opened('\uFEFF---\r\n# 注释\r\ntags: [甲, 乙]\r\n---\r\n# 原文\r\n')
  assert.equal(session.text, '---\n# 注释\ntags: [甲, 乙]\n---\n# 原文\n')
  await session.save({ save() { assert.fail('未修改不能写盘') } })
  session.text += '新增\n'
  assert.equal(session.rawContent(), '\uFEFF---\r\n# 注释\r\ntags: [甲, 乙]\r\n---\r\n# 原文\r\n新增\r\n')
})

test('未保存修改遇外部更新保留原基线和本地文本', async () => {
  const session = opened()
  session.text = '# 本地\n'
  await session.check({ version: async () => ({ exists: true, version: 'v2' }), read: async () => detail('# 磁盘\n', 'v2') })
  assert.equal(session.text, '# 本地\n')
  assert.equal(session.baseline.version, 'v1')
  assert.equal(session.external.raw_content, '# 磁盘\n')
  let savedVersion
  await session.save({ save: async (path, raw, version) => { savedVersion = version; throw new Error('409') } }).catch(() => {})
  assert.equal(savedVersion, 'v1')
  assert.equal(session.dirty, true)
})

test('干净文档自动刷新；外部删除保留文本且不能隐式新建', async () => {
  const session = opened()
  await session.check({ version: async () => ({ exists: true, version: 'v2' }), read: async () => detail('# 磁盘\n', 'v2') })
  assert.equal(session.text, '# 磁盘\n')
  assert.equal(session.baseline.version, 'v2')
  await session.check({ version: async () => ({ exists: false, version: null }) })
  assert.equal(session.missing, true)
  assert.equal(session.text, '# 磁盘\n')
  session.text += '修改'
  await assert.rejects(session.save({ create() { assert.fail('不能重建删除文件') }, save: async () => { throw new Error('404') } }), /404/)
})

test('已切换会话忽略旧读取与轮询结果', async () => {
  const session = opened()
  const pending = deferred()
  const checking = session.check({ version: () => pending.promise, read: async () => detail('# 旧响应\n', 'v2') })
  const oldGeneration = session.generation
  session.begin('blog/新文件.md')
  session.load(detail('# 新文件\n', 'new', 'blog/新文件.md'), session.generation)
  session.load(detail('# 过期加载\n'), oldGeneration)
  pending.resolve({ exists: true, version: 'v2' })
  await checking
  assert.equal(session.path, 'blog/新文件.md')
  assert.equal(session.text, '# 新文件\n')
})

test('保存过程中继续输入不会被响应覆盖，新基线仍是已保存快照', async () => {
  const session = opened()
  session.text = '# 已发送\n'
  const pending = deferred()
  const saving = session.save({ save: () => pending.promise })
  session.text = '# 保存期间输入\n'
  pending.resolve(detail('# 已发送\n', 'v2'))
  await saving
  assert.equal(session.text, '# 保存期间输入\n')
  assert.equal(session.baseline.raw_content, '# 已发送\n')
  assert.equal(session.baseline.version, 'v2')
  assert.equal(session.dirty, true)
})

test('同一文档合并轮询请求，暂时读取失败保留基线', async () => {
  const session = opened()
  const pending = deferred()
  let reads = 0
  const api = { version: () => { reads++; return pending.promise }, read: async () => { throw new Error('YAML 未写完') } }
  const first = session.check(api)
  const second = session.check(api)
  pending.resolve({ exists: true, version: 'v2' })
  await Promise.allSettled([first, second])
  assert.equal(reads, 1)
  assert.equal(session.text, '# 原文\n')
  assert.equal(session.baseline.version, 'v1')
})

test('新建排他创建且保存失败保留缓冲', async () => {
  const session = new DocumentSession()
  session.begin(null)
  session.text = '# 新文档\n'
  await assert.rejects(session.save({ create: async () => { throw new Error('同名') } }, 'blog/中文 空格.md'), /同名/)
  assert.equal(session.dirty, true)
  assert.equal(session.path, null)
  await session.save({ create: async (path, raw) => detail(raw, 'created', path) }, 'blog/中文 空格.md')
  assert.equal(session.path, 'blog/中文 空格.md')
  assert.equal(session.dirty, false)
})

test('保存完成之前发出的轮询不能把新基线回退', async () => {
  const session = opened()
  const pending = deferred()
  const checking = session.check({ version: () => pending.promise, read: async () => detail('# 旧磁盘\n', 'old') })
  session.text = '# 新保存\n'
  await session.save({ save: async () => detail('# 新保存\n', 'v2') })
  pending.resolve({ exists: true, version: 'old' })
  await checking
  assert.equal(session.baseline.version, 'v2')
  assert.equal(session.external, null)
})

test('另存为使用排他创建且保留请求期间的新输入', async () => {
  const session = opened('\uFEFF# 原文\r\n')
  session.text = '# 另存内容\n'
  const pending = deferred()
  let sent
  const saving = session.saveAs({ create: async (path, raw) => { sent = { path, raw }; return pending.promise } }, 'blog/另存.md')
  session.text += '继续输入\n'
  pending.resolve(detail('# 另存内容\n', 'new', 'blog/另存.md'))
  await saving
  assert.deepEqual(sent, { path: 'blog/另存.md', raw: '# 另存内容\n' })
  assert.equal(session.path, 'blog/另存.md')
  assert.equal(session.text, '# 另存内容\n继续输入\n')
  assert.equal(session.dirty, true)
})

test('保存旧会话的响应不能污染新打开的文件', async () => {
  const session = opened()
  session.text = '# 发送\n'
  const pending = deferred()
  const saving = session.save({ save: () => pending.promise })
  session.begin('blog/新文件.md')
  session.load(detail('# 新文件\n', 'new', 'blog/新文件.md'), session.generation)
  pending.resolve(detail('# 发送\n', 'v2'))
  await saving
  assert.equal(session.path, 'blog/新文件.md')
  assert.equal(session.text, '# 新文件\n')
  assert.equal(session.baseline.version, 'new')
})

test('新建文件将粘贴的BOM与CRLF规范为无BOM的LF', async () => {
  const session = new DocumentSession()
  session.begin(null)
  session.text = '\uFEFF# 粘贴\r\n'
  let sent
  await session.save({ create: async (path, raw) => { sent = raw; return detail(raw, 'new', path) } }, 'blog/新文件.md')
  assert.equal(sent, '# 粘贴\n')
})

test('自动新建模板是草稿基线，作者修改后才提示未保存', () => {
  const session = new DocumentSession()
  session.begin(null, '---\ntitle: ""\n---\n\n# \n')
  assert.equal(session.text, '---\ntitle: ""\n---\n\n# \n')
  assert.equal(session.dirty, false)
  session.text += '正文'
  assert.equal(session.dirty, true)
})

test('用途切换仅替换干净自动草稿，不能覆盖作者输入', () => {
  const session = new DocumentSession()
  session.begin(null, '自动模板')
  assert.equal(session.replaceDraft(''), true)
  assert.equal(session.dirty, false)
  session.text = '作者正文'
  assert.equal(session.replaceDraft('新模板'), false)
  assert.equal(session.text, '作者正文')
  assert.equal(session.dirty, true)
})

test('新建显式传文章用途，另存默认按复制保留历史日期', async () => {
  const session = new DocumentSession()
  session.begin(null, 'date: "2020-01-01T10:00:00+08:00"\nupdated: "2021-01-01T10:00:00+08:00"\n')
  const requests = []
  const api = { create: async (path, raw, article) => { requests.push({ path, raw, article }); return detail(raw, 'created', path) } }
  await session.save(api, 'blog/说明.md', false)
  assert.equal(requests[0].article, false)
  await session.saveAs(api, 'blog/复制.md')
  assert.equal(requests[1].article, false)
  assert.equal(requests[1].raw, 'date: "2020-01-01T10:00:00+08:00"\nupdated: "2021-01-01T10:00:00+08:00"\n')
  session.begin(null)
  session.text = '# 新文章\n'
  await session.save(api, 'blog/新文章.md', true)
  assert.equal(requests[2].article, true)
})

test('保存期间新输入合并服务端updated，下次保存不回退时间', async () => {
  const raw = '---\ndate: "2020-01-01T10:00:00+08:00"\nupdated: "2021-01-01T10:00:00+08:00" # 保留注释\n---\n# 原文\n'
  const session = opened('\uFEFF' + raw.replace(/\n/g, '\r\n'))
  session.text += '已发送\n'
  const pending = deferred()
  const saving = session.save({ save: () => pending.promise })
  session.text += '期间输入\n'
  const saved = (raw + '已发送\n').replace('2021-01-01T10:00:00+08:00', '2026-10-29T12:34:56+08:00')
  pending.resolve(detail('\uFEFF' + saved.replace(/\n/g, '\r\n'), 'v2'))
  await saving
  assert.equal(session.text, saved + '期间输入\n')
  assert.equal(session.dirty, true)
  let sent
  await session.save({ save: async (path, content) => { sent = content; return detail(content, 'v3') } })
  assert.equal(sent, '\uFEFF' + (saved + '期间输入\n').replace(/\n/g, '\r\n'))
})

test('保存期间作者自行修改updated时不被服务端响应覆盖', async () => {
  const raw = '---\nupdated: "2021-01-01T10:00:00+08:00"\n---\n# 原文\n'
  const session = opened(raw)
  session.text += '已发送\n'
  const pending = deferred()
  const saving = session.save({ save: () => pending.promise })
  session.text = session.text.replace('2021-01-01', '2025-01-01')
  pending.resolve(detail((raw + '已发送\n').replace('2021-01-01', '2026-10-29'), 'v2'))
  await saving
  assert.match(session.text, /updated: "2025-01-01/)
})

test('说明文档新建后本次编辑继续显式说明用途', async () => {
  const session = new DocumentSession()
  session.begin(null)
  session.text = '---\ntitle: "说明"\ndate: "2020-01-01T10:00:00+08:00"\nupdated: "2021-01-01T10:00:00+08:00"\ndescription: "说明"\ntags: []\nsticky: false\n---\n# 说明\n'
  const requests = []
  const api = {
    create: async (path, raw, article) => { requests.push({ method: 'POST', article }); return detail(raw, 'v1', path) },
    save: async (path, raw, version, article) => { requests.push({ method: 'PUT', article }); return detail(raw, 'v2', path) }
  }
  await session.save(api, 'blog/说明.md', false)
  session.text += '修改说明\n'
  await session.save(api, undefined, false)
  assert.deepEqual(requests, [{ method: 'POST', article: false }, { method: 'PUT', article: false }])
})

test('既有文档默认自动判断，明确普通或说明则传递本次用途', async () => {
  for (const article of [undefined, true, false]) {
    const session = opened()
    session.text += '修改\n'
    let received
    await session.save({ save: async (path, raw, version, purpose) => { received = purpose; return detail(raw, 'v2', path) } }, undefined, article)
    assert.equal(received, article)
  }
})

test('内容API仅在明确选择时发送PUT article字段，保留false', async () => {
  const originalFetch = globalThis.fetch
  const requests = []
  globalThis.fetch = async (_url, options) => {
    requests.push(JSON.parse(options.body))
    return new Response(JSON.stringify(detail()), { status: 200, headers: { 'Content-Type': 'application/json' } })
  }
  try {
    await contentApi.save('blog/文档.md', '# 原文\n', 'v1')
    await contentApi.save('blog/文档.md', '# 原文\n', 'v1', true)
    await contentApi.save('blog/文档.md', '# 原文\n', 'v1', false)
    assert.deepEqual(requests, [
      { relative_path: 'blog/文档.md', raw_content: '# 原文\n', expected_version: 'v1' },
      { relative_path: 'blog/文档.md', raw_content: '# 原文\n', expected_version: 'v1', article: true },
      { relative_path: 'blog/文档.md', raw_content: '# 原文\n', expected_version: 'v1', article: false }
    ])
  } finally { globalThis.fetch = originalFetch }
})
