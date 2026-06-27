'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const registryPath = path.join(root, 'config', 'category-registry.json');
const postsRoot = path.join(root, 'source', '_posts');
const shouldWrite = process.argv.includes('--write');

function readRegistry() {
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  const map = new Map();
  for (const primary of registry) {
    for (const child of primary.children || []) {
      map.set(`${primary.note_prefix1}-${child.note_prefix2}`, {
        primaryName: primary.frontend_name1,
        secondaryName: child.frontend_name2,
      });
    }
  }
  return map;
}

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(fullPath));
    if (entry.isFile() && entry.name.endsWith('.md')) files.push(fullPath);
  }
  return files;
}

function getPrefixKey(filePath) {
  const baseName = path.basename(filePath, '.md');
  const parts = baseName.split('-', 3);
  if (parts.length < 2) return null;
  return `${parts[0]}-${parts[1]}`;
}

function syncFile(filePath, registryMap) {
  const key = getPrefixKey(filePath);
  if (!key || !registryMap.has(key)) return null;

  const target = registryMap.get(key);
  const content = fs.readFileSync(filePath, 'utf8');
  const fmMatch = content.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  if (!fmMatch) return null;

  const fm = fmMatch[1];
  const categoriesPattern = /categories:\s*\r?\n\s*-\s*\[\s*([^\],]+)\s*,\s*([^\]]+)\s*\]/;
  const match = fm.match(categoriesPattern);
  if (!match) return null;

  const currentPrimary = match[1].trim();
  const currentSecondary = match[2].trim();
  if (currentPrimary === target.primaryName && currentSecondary === target.secondaryName) {
    return null;
  }

  const nextFm = fm.replace(
    categoriesPattern,
    `categories:\n  - [${target.primaryName}, ${target.secondaryName}]`
  );
  const nextContent = content.replace(fmMatch[1], nextFm);

  if (shouldWrite) {
    fs.writeFileSync(filePath, nextContent, 'utf8');
  }

  return {
    filePath,
    from: `${currentPrimary} / ${currentSecondary}`,
    to: `${target.primaryName} / ${target.secondaryName}`,
  };
}

function main() {
  const registryMap = readRegistry();
  const changes = walk(postsRoot)
    .map((filePath) => syncFile(filePath, registryMap))
    .filter(Boolean);

  const mode = shouldWrite ? '写入' : '预览';
  console.log(`${mode}: ${changes.length} 篇文章需要同步分类`);
  for (const change of changes) {
    console.log(`- ${path.relative(root, change.filePath)}: ${change.from} -> ${change.to}`);
  }
  if (!shouldWrite) {
    console.log('\n确认无误后执行: node scripts/sync-categories-from-registry.cjs --write');
  }
}

if (require.main === module) {
  main();
}
