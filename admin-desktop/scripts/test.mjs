import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { spawnSync } from 'node:child_process'
import ts from 'typescript'

const directory = await mkdtemp(join(tmpdir(), 'desktop-content-tests-'))
try {
  for (const name of ['utils/documentSession', 'utils/documentSession.test', 'utils/contentOrder', 'utils/contentOrder.test', 'utils/articleTemplate', 'utils/articleTemplate.test', 'api/content']) {
    const source = await readFile(new URL(`../src/${name}.ts`, import.meta.url), 'utf8')
    const output = ts.transpileModule(source, {
      compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext }
    }).outputText.replace(/from '(\.{1,2}\/[^']+)'/g, "from '$1.mjs'")
    await mkdir(dirname(join(directory, `${name}.mjs`)), { recursive: true })
    await writeFile(join(directory, `${name}.mjs`), output)
  }
  const result = spawnSync(process.execPath, ['--test', join(directory, 'utils/documentSession.test.mjs'), join(directory, 'utils/contentOrder.test.mjs'), join(directory, 'utils/articleTemplate.test.mjs')], { stdio: 'inherit' })
  process.exitCode = result.status ?? 1
} finally {
  await rm(directory, { recursive: true, force: true })
}
