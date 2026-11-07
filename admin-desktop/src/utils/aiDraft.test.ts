// @ts-nocheck -- Node 测试通过脚本转译运行，不进入浏览器。
import assert from 'node:assert/strict'
import test from 'node:test'
import { AiDraftSession } from './aiDraft'

test('rewrite sends only the current body and preserves the exact YAML prefix', () => {
  const prefix = '\uFEFF---\r\n# comment\r\ntitle: "Keep"\r\nextra:\r\n  - nested\r\n---\r\n'
  const state = new AiDraftSession()
  const request = state.begin('rewrite', prefix + '\r\n# Keep\r\nUnsaved text', 1)
  assert.equal(request.before, '\r\n# Keep\r\nUnsaved text')
  assert.equal(state.complete(request, '# Keep\nRevised text'), true)
  assert.equal(state.accept(prefix + '\r\n# Keep\r\nUnsaved text', 1), prefix + '\r\n# Keep\r\nRevised text')
})

test('generated YAML cannot replace original YAML or introduce a new header', () => {
  const state = new AiDraftSession()
  const request = state.begin('generate', 'old', 1)
  assert.equal(state.complete(request, '---\ntitle: rejected\n---\n# New body\n'), true)
  assert.equal(state.accept('old', 1), '# New body\n')
})

test('an incomplete YAML header is rejected before the editor buffer can change', () => {
  const state = new AiDraftSession()
  assert.throws(() => state.begin('rewrite', '---\ntitle: incomplete', 1))
  const request = state.begin('generate', 'untouched', 1)
  assert.throws(() => state.complete(request, '---\ntitle: incomplete'))
  assert.equal(state.accept('untouched', 1), null)
})

test('edits invalidate pending responses even if the same text is restored', () => {
  const state = new AiDraftSession()
  const first = state.begin('rewrite', 'first', 1)
  state.invalidate()
  const second = state.begin('rewrite', 'first', 1)
  assert.equal(state.complete(first, 'late'), false)
  assert.equal(state.complete(second, 'current'), true)
  assert.equal(state.accept('first', 1), 'current')
})

test('current buffer and document must still match when accepting a suggestion', () => {
  const state = new AiDraftSession()
  const request = state.begin('rewrite', 'first', 1)
  state.complete(request, 'suggestion')
  assert.equal(state.accept('edited', 1), null)
  assert.equal(state.accept('first', 2), null)
  assert.equal(state.accept('first', 1), 'suggestion')
  assert.equal(state.accept('first', 1), null)
})
test('generation starts the body on a separate line after a YAML delimiter at EOF', () => {
  const state = new AiDraftSession()
  const header = '---\r\ntitle: Header\r\n---'
  const request = state.begin('generate', header, 1)
  state.complete(request, '# Header\nNew text')
  assert.equal(state.accept(header, 1), header + '\r\n# Header\r\nNew text')
})
