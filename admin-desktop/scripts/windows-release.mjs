import { createHash, createPublicKey, verify } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const desktop = fileURLToPath(new URL('../', import.meta.url))
const versionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/

function required(env, name, valid = () => true) {
  const value = env[name]?.trim()
  if (!value || !valid(value)) throw new Error(`缺少或无效的发布配置 ${name}`)
  return value
}

function isHttps(value) {
  const url = URL.parse(value)
  return url?.protocol === 'https:' && !url.username && !url.password && !url.hash
}

function tauriPublicKey(value) {
  const outer = Buffer.from(value, 'base64')
  if (outer.toString('base64') !== value) return
  const [comment, encoded, extra] = outer.toString('utf8').trimEnd().split(/\r?\n/)
  const key = Buffer.from(encoded ?? '', 'base64')
  if (extra === undefined && comment.startsWith('untrusted comment: ') && key.length === 42 && key.subarray(0, 2).toString() === 'Ed') return key
}

export function releaseConfig(env) {
  const certificateThumbprint = required(env, 'LUCHUAN_CODESIGN_THUMBPRINT', value => /^[\da-f]{40}$/i.test(value))
  const timestampUrl = required(env, 'LUCHUAN_CODESIGN_TIMESTAMP_URL', isHttps)
  const endpoint = required(env, 'LUCHUAN_UPDATER_ENDPOINT', isHttps)
  const pubkey = required(env, 'LUCHUAN_UPDATER_PUBLIC_KEY', tauriPublicKey)
  required(env, 'TAURI_SIGNING_PRIVATE_KEY')
  return {
    bundle: {
      createUpdaterArtifacts: true,
      windows: { certificateThumbprint, digestAlgorithm: 'sha256', timestampUrl, tsp: true },
    },
    plugins: {
      updater: { pubkey, endpoints: [endpoint], requireSignedVersion: true, windows: { installMode: 'passive' } },
    },
  }
}

function assetName(version) {
  return `luchuan-admin_${version}_x64-setup.exe`
}

export function verifyUpdaterSignature(pubkey, encoded, digest, version) {
  const key = tauriPublicKey(pubkey)
  const [, signatureLine = '', commentLine = '', globalLine = ''] = Buffer.from(encoded, 'base64').toString('utf8').split(/\r?\n/)
  const packet = Buffer.from(signatureLine, 'base64')
  const commentPrefix = 'trusted comment: '
  const comment = commentLine.slice(commentPrefix.length)
  if (!key || packet.length !== 74 || packet.subarray(0, 2).toString() !== 'ED'
      || !packet.subarray(2, 10).equals(key.subarray(2, 10)) || !commentLine.startsWith(commentPrefix)
      || !comment.endsWith(`\tversion:${version}`)) {
    throw new Error('Tauri 更新签名与发布公钥或版本不匹配')
  }
  // Minisign 的公开密钥为 32 字节 Ed25519 公钥，前缀为 RFC 8410 SPKI。
  const spki = Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), key.subarray(10)])
  const publicKey = createPublicKey({ key: spki, format: 'der', type: 'spki' })
  const signature = packet.subarray(10)
  if (!verify(null, digest, publicKey, signature)
      || !verify(null, Buffer.concat([signature, Buffer.from(comment)]), publicKey, Buffer.from(globalLine, 'base64'))) {
    throw new Error('Tauri 更新签名校验失败')
  }
}

export function updateManifest({ repository, tag, version, notes, signature, date }) {
  if (!versionPattern.test(version) || tag !== `desktop-v${version}`) throw new Error('桌面发布标签与版本不一致')
  if (!/^[\w.-]+\/[\w.-]+$/.test(repository)) throw new Error('缺少或无效的 GitHub 发布仓库')
  if (!signature?.trim()) throw new Error('缺少 Tauri 更新签名')
  return {
    version,
    notes,
    pub_date: date,
    platforms: {
      'windows-x86_64-nsis': {
        signature: signature.trim(),
        url: `https://github.com/${repository}/releases/download/${tag}/${assetName(version)}`,
      },
    },
  }
}

async function main([command, output, installer, notesPath], env) {
  if (command === 'config') {
    await writeFile(output, JSON.stringify(releaseConfig(env)))
    return
  }
  if (command !== 'stage') throw new Error('用法：windows-release.mjs config <文件> 或 stage <目录> <安装包> <发布说明>')

  const { version } = JSON.parse(await readFile(join(desktop, 'src-tauri/tauri.conf.json'), 'utf8'))
  const notes = await readFile(notesPath, 'utf8')
  const signature = await readFile(`${installer}.sig`, 'utf8')
  const manifest = updateManifest({
    repository: env.GITHUB_REPOSITORY, tag: env.LUCHUAN_RELEASE_TAG, version, notes, signature, date: new Date().toISOString(),
  })
  const name = assetName(version)
  const hash = createHash('sha256')
  const updateHash = createHash('blake2b512')
  for await (const chunk of createReadStream(installer)) {
    hash.update(chunk)
    updateHash.update(chunk)
  }
  verifyUpdaterSignature(required(env, 'LUCHUAN_UPDATER_PUBLIC_KEY', tauriPublicKey), signature, updateHash.digest(), version)
  await mkdir(output, { recursive: true })
  await copyFile(installer, join(output, name))
  await writeFile(join(output, `${name}.sig`), signature.trim())
  await writeFile(join(output, 'latest.json'), JSON.stringify(manifest, null, 2) + '\n')
  await writeFile(join(output, 'SHA256SUMS.txt'), `${hash.digest('hex')}  ${name}\n`)
  await copyFile(notesPath, join(output, 'release-notes.md'))
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main(process.argv.slice(2), process.env)
}
