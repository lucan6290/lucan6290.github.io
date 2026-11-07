import assert from 'node:assert/strict'
import { createHash, generateKeyPairSync, sign } from 'node:crypto'
import test from 'node:test'
import * as release from './windows-release.mjs'
const { releaseConfig, updateManifest } = release

const keyBytes = Buffer.concat([Buffer.from('Ed'), Buffer.alloc(40, 42)])
const pubkey = Buffer.from(`untrusted comment: test fixture\n${keyBytes.toString('base64')}\n`).toString('base64')
const config = {
  LUCHUAN_CODESIGN_THUMBPRINT: '42'.repeat(20),
  LUCHUAN_CODESIGN_TIMESTAMP_URL: 'https://timestamp.example.test',
  LUCHUAN_UPDATER_ENDPOINT: 'https://releases.example.test/desktop/latest.json',
  LUCHUAN_UPDATER_PUBLIC_KEY: pubkey,
  TAURI_SIGNING_PRIVATE_KEY: 'test fixture',
}

test('发行构建将固定 HTTPS 频道、公钥和签名版本写入配置', () => {
  const release = releaseConfig(config)
  assert.deepEqual(release.plugins.updater, {
    pubkey,
    endpoints: [config.LUCHUAN_UPDATER_ENDPOINT],
    requireSignedVersion: true,
    windows: { installMode: 'passive' },
  })
  assert.deepEqual(release.bundle.windows, {
    certificateThumbprint: config.LUCHUAN_CODESIGN_THUMBPRINT,
    digestAlgorithm: 'sha256',
    timestampUrl: config.LUCHUAN_CODESIGN_TIMESTAMP_URL,
    tsp: true,
  })
  assert.equal(release.bundle.createUpdaterArtifacts, true)
})

test('发行构建拒绝缺少凭据、无效公钥或不安全的频道和时间戳地址', () => {
  for (const name of Object.keys(config)) {
    assert.throws(() => releaseConfig({ ...config, [name]: '' }), new RegExp(name))
  }
  assert.throws(() => releaseConfig({ ...config, LUCHUAN_UPDATER_PUBLIC_KEY: 'invalid' }), /LUCHUAN_UPDATER_PUBLIC_KEY/)
  assert.throws(() => releaseConfig({ ...config, LUCHUAN_UPDATER_ENDPOINT: 'http://example.test/latest.json' }), /LUCHUAN_UPDATER_ENDPOINT/)
  assert.throws(() => releaseConfig({ ...config, LUCHUAN_UPDATER_ENDPOINT: 'https://user:secret@example.test/latest.json' }), /LUCHUAN_UPDATER_ENDPOINT/)
  assert.throws(() => releaseConfig({ ...config, LUCHUAN_CODESIGN_TIMESTAMP_URL: 'http://example.test' }), /LUCHUAN_CODESIGN_TIMESTAMP_URL/)
})

test('更新清单只指向同标签下的 Windows x64 NSIS 安装包', () => {
  const manifest = updateManifest({
    repository: 'lucan6290/lucan6290.github.io',
    tag: 'desktop-v0.1.0',
    version: '0.1.0',
    notes: '桌面更新',
    signature: 'signature bytes',
    date: '2026-11-07T00:00:00Z',
  })
  assert.equal(manifest.version, '0.1.0')
  assert.equal(manifest.notes, '桌面更新')
  assert.equal(manifest.pub_date, '2026-11-07T00:00:00Z')
  assert.deepEqual(manifest.platforms, {
    'windows-x86_64-nsis': {
      url: 'https://github.com/lucan6290/lucan6290.github.io/releases/download/desktop-v0.1.0/luchuan-admin_0.1.0_x64-setup.exe',
      signature: 'signature bytes',
    },
  })
})

test('拒绝非桌面标签、标签与版本不一致及空签名', () => {
  const args = { repository: 'owner/repo', version: '0.1.0', tag: 'desktop-v0.1.0', signature: 'signature' }
  assert.throws(() => updateManifest({ ...args, tag: 'v0.1.0' }), /标签/)
  assert.throws(() => updateManifest({ ...args, tag: 'desktop-v0.1.1' }), /标签/)
  assert.throws(() => updateManifest({ ...args, signature: '' }), /签名/)
})

test('验证最终安装包字节、公钥以及签名内的版本', () => {
  const { privateKey, publicKey } = generateKeyPairSync('ed25519')
  const id = Buffer.alloc(8, 42)
  const rawKey = publicKey.export({ type: 'spki', format: 'der' }).subarray(-32)
  const encodedKey = Buffer.concat([Buffer.from('Ed'), id, rawKey]).toString('base64')
  const tauriKey = Buffer.from(`untrusted comment: test fixture\n${encodedKey}\n`).toString('base64')
  const digest = createHash('blake2b512').update('installer bytes').digest()
  const signature = sign(null, digest, privateKey)
  const trustedComment = 'timestamp:0\tfile:fixture.exe\tversion:0.1.0'
  const trustedSignature = sign(null, Buffer.concat([signature, Buffer.from(trustedComment)]), privateKey)
  const rawSignature = Buffer.concat([Buffer.from('ED'), id, signature]).toString('base64')
  const tauriSignature = Buffer.from(`untrusted comment: test fixture\n${rawSignature}\ntrusted comment: ${trustedComment}\n${trustedSignature.toString('base64')}\n`).toString('base64')
  assert.doesNotThrow(() => release.verifyUpdaterSignature(tauriKey, tauriSignature, digest, '0.1.0'))
  assert.throws(() => release.verifyUpdaterSignature(tauriKey, tauriSignature, Buffer.alloc(64), '0.1.0'), /签名/)
  assert.throws(() => release.verifyUpdaterSignature(pubkey, tauriSignature, digest, '0.1.0'), /签名/)
  assert.throws(() => release.verifyUpdaterSignature(tauriKey, tauriSignature, digest, '0.2.0'), /签名/)
})
