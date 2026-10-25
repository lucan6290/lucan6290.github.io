#!/usr/bin/env node
// 从 old/site 复制静态资源到 frontend/public/。
// 1. old/site/static/ → frontend/public/（favicon、covers 等）
// 2. old/site/docs/ 下的图片 → frontend/content/knowledge/ 对应位置（文章内嵌图片）
// 用法：node scripts/copy-static-assets.mjs [--dry-run]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OLD_SITE = path.resolve(ROOT, '..', 'old', 'site');
const PUBLIC_OUT = path.join(ROOT, 'public');
const CONTENT_OUT = path.join(ROOT, 'content', 'knowledge');

const DRY_RUN = process.argv.includes('--dry-run');

function copyFile(src, dest) {
  if (fs.existsSync(dest)) {
    console.log(`  [exists] ${path.relative(ROOT, dest)}`);
    return false;
  }
  if (DRY_RUN) {
    console.log(`  [dry-run] ${path.relative(OLD_SITE, src)} → ${path.relative(ROOT, dest)}`);
    return true;
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  console.log(`  [copy] ${path.relative(OLD_SITE, src)} → ${path.relative(ROOT, dest)}`);
  return true;
}

function walkFiles(dir, extFilter) {
  if (!fs.existsSync(dir)) return [];
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walkFiles(full, extFilter));
    } else if (!extFilter || extFilter.test(entry.name)) {
      results.push(full);
    }
  }
  return results;
}

console.log(`\n=== Static Assets Copy ===`);
console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}\n`);

// 1. static/ → public/
let copied = 0;
const staticDir = path.join(OLD_SITE, 'static');
if (fs.existsSync(staticDir)) {
  console.log('[static → public]');
  for (const f of walkFiles(staticDir)) {
    const rel = path.relative(staticDir, f);
    if (copyFile(f, path.join(PUBLIC_OUT, rel))) copied++;
  }
} else {
  console.log('[skip] old/site/static/ not found');
}

// 2. docs 内嵌图片 → content/knowledge 对应位置
console.log('\n[docs imgs → content/knowledge]');
const docsDir = path.join(OLD_SITE, 'docs');
if (fs.existsSync(docsDir)) {
  const imgs = walkFiles(docsDir, /\.(png|jpg|jpeg|gif|svg|webp)$/i);
  for (const img of imgs) {
    const rel = path.relative(docsDir, img);
    if (copyFile(img, path.join(CONTENT_OUT, rel))) copied++;
  }
} else {
  console.log('[skip] old/site/docs/ not found');
}

console.log(`\n=== Done: ${copied} files copied ===`);
if (DRY_RUN) {
  console.log(`⚠️  This was a dry run. Remove --dry-run to actually copy files.`);
}
