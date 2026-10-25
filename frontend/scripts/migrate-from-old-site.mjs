#!/usr/bin/env node
/**
 * 从 old/site 迁移内容到 frontend/content/。
 *
 * 映射规则：
 *   old/site/docs/<category>/... → frontend/content/knowledge/<category>/...
 *   old/site/blog/<category>/... → frontend/content/blog/<category>/...
 *
 * - 保留 frontmatter 原文
 * - 保留目录层级
 * - 跳过 index.md（分类索引页由新前端自动生成）
 * - 不覆盖已存在的目标文件（安全重跑）
 * - 自动为无数字前缀的文件名添加递增前缀（按源目录内字母序）
 *
 * 用法：node scripts/migrate-from-old-site.mjs [--dry-run]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OLD_SITE = path.resolve(ROOT, '..', 'old', 'site');
const CONTENT_OUT = path.join(ROOT, 'content');

const DRY_RUN = process.argv.includes('--dry-run');
const MD_EXT = /\.(md|mdx)$/i;
const NUMERIC_PREFIX = /^(\d+)[-_]/;

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name.startsWith('_')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walk(full));
    } else if (MD_EXT.test(entry.name)) {
      results.push(full);
    }
  }
  return results;
}

function needsPrefix(name) {
  return !NUMERIC_PREFIX.test(name);
}

function addPrefix(name, index) {
  const ext = path.extname(name);
  const base = path.basename(name, ext);
  return `${String(index + 1).padStart(2, '0')}-${base}${ext}`;
}

function migrate(sourceRoot, targetRoot, label) {
  if (!fs.existsSync(sourceRoot)) {
    console.log(`[skip] ${label}: source not found (${sourceRoot})`);
    return { copied: 0, skipped: 0 };
  }

  const files = walk(sourceRoot);
  let copied = 0;
  let skipped = 0;

  // 按父目录分组，为无前缀文件分配递增序号
  const byParent = new Map();
  for (const f of files) {
    const parent = path.dirname(f);
    if (!byParent.has(parent)) byParent.set(parent, []);
    byParent.get(parent).push(f);
  }

  for (const [parent, siblings] of byParent) {
    // 按文件名排序，保证前缀分配稳定
    siblings.sort((a, b) => path.basename(a).localeCompare(path.basename(b)));
    let autoIdx = 0;

    for (const srcFile of siblings) {
      const relDir = path.relative(sourceRoot, parent);
      const fileName = path.basename(srcFile);

      // 跳过 index.md（分类索引页）
      if (/^index\.mdx?$/i.test(fileName)) {
        skipped++;
        continue;
      }

      const outName = needsPrefix(fileName) ? addPrefix(fileName, autoIdx++) : fileName;
      const outDir = path.join(targetRoot, relDir);
      const outFile = path.join(outDir, outName);

      if (fs.existsSync(outFile)) {
        console.log(`  [exists] ${path.relative(CONTENT_OUT, outFile)}`);
        skipped++;
        continue;
      }

      if (DRY_RUN) {
        console.log(`  [dry-run] ${path.relative(sourceRoot, srcFile)} → ${path.relative(CONTENT_OUT, outFile)}`);
      } else {
        fs.mkdirSync(outDir, { recursive: true });
        fs.copyFileSync(srcFile, outFile);
        console.log(`  [copy] ${path.relative(sourceRoot, srcFile)} → ${path.relative(CONTENT_OUT, outFile)}`);
      }
      copied++;
    }
  }

  console.log(`[${label}] ${copied} copied, ${skipped} skipped.`);
  return { copied, skipped };
}

console.log(`\n=== Content Migration ===`);
console.log(`Source: ${OLD_SITE}`);
console.log(`Target: ${CONTENT_OUT}`);
console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}\n`);

const docsResult = migrate(path.join(OLD_SITE, 'docs'), path.join(CONTENT_OUT, 'knowledge'), 'docs → knowledge');
const blogResult = migrate(path.join(OLD_SITE, 'blog'), path.join(CONTENT_OUT, 'blog'), 'blog → blog');

console.log(`\n=== Done ===`);
console.log(`Total: ${docsResult.copied + blogResult.copied} copied, ${docsResult.skipped + blogResult.skipped} skipped.`);
if (DRY_RUN) {
  console.log(`\n⚠️  This was a dry run. Remove --dry-run to actually copy files.`);
}
