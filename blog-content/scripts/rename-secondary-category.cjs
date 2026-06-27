'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_PRIMARY = '技术研习';
const DEFAULT_OLD_SECONDARY = 'Jetson Orin NANO 开发板使用笔记';
const DEFAULT_NEW_SECONDARY = 'Jetson_Orin_NANO';

const POSTS_DIR = path.resolve(__dirname, '..', 'source', '_posts');

function parseArgs(argv) {
  const args = {
    primary: DEFAULT_PRIMARY,
    oldSecondary: DEFAULT_OLD_SECONDARY,
    newSecondary: DEFAULT_NEW_SECONDARY,
    write: false
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--write') {
      args.write = true;
    } else if (arg === '--primary') {
      args.primary = argv[++i];
    } else if (arg === '--old') {
      args.oldSecondary = argv[++i];
    } else if (arg === '--new') {
      args.newSecondary = argv[++i];
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`未知参数: ${arg}`);
    }
  }

  if (!args.primary || !args.oldSecondary || !args.newSecondary) {
    throw new Error('primary、oldSecondary、newSecondary 不能为空');
  }

  return args;
}

function printHelp() {
  console.log(`
用法:
  node scripts/rename-secondary-category.cjs [选项]

默认行为:
  预览将「技术研习 / Jetson Orin NANO 开发板使用笔记」改为「技术研习 / Jetson_Orin_NANO」的文章。

选项:
  --write              实际写入文件；不加时只预览
  --primary <名称>     一级分类，默认: 技术研习
  --old <名称>         旧二级分类，默认: Jetson Orin NANO 开发板使用笔记
  --new <名称>         新二级分类，默认: Jetson_Orin_NANO
  --help              显示帮助

示例:
  node scripts/rename-secondary-category.cjs
  node scripts/rename-secondary-category.cjs --write
  node scripts/rename-secondary-category.cjs --old "旧二级分类" --new "新二级分类" --write
`);
}

function walkMarkdownFiles(dir) {
  if (!fs.existsSync(dir)) return [];

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }

  return files;
}

function splitFrontMatter(content) {
  if (!content.startsWith('---')) return null;

  const firstBreak = content.indexOf('\n');
  if (firstBreak === -1) return null;

  const endMarker = content.indexOf('\n---', firstBreak + 1);
  if (endMarker === -1) return null;

  const endLineBreak = content.indexOf('\n', endMarker + 1);
  const frontMatterEnd = endLineBreak === -1 ? content.length : endLineBreak + 1;

  return {
    frontMatter: content.slice(0, frontMatterEnd),
    body: content.slice(frontMatterEnd)
  };
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function renameCategoryInFrontMatter(frontMatter, primary, oldSecondary, newSecondary) {
  const primaryPattern = escapeRegExp(primary);
  const oldPattern = escapeRegExp(oldSecondary);

  const inlineNestedCategory = new RegExp(
    `(\\[\\s*${primaryPattern}\\s*,\\s*)${oldPattern}(\\s*\\])`,
    'g'
  );

  const updated = frontMatter.replace(inlineNestedCategory, `$1${newSecondary}$2`);
  return {
    updated,
    changed: updated !== frontMatter
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const files = walkMarkdownFiles(POSTS_DIR);
  const changedFiles = [];

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const parts = splitFrontMatter(content);
    if (!parts) continue;

    const result = renameCategoryInFrontMatter(
      parts.frontMatter,
      args.primary,
      args.oldSecondary,
      args.newSecondary
    );

    if (!result.changed) continue;

    changedFiles.push(file);
    if (args.write) {
      fs.writeFileSync(file, result.updated + parts.body, 'utf8');
    }
  }

  const mode = args.write ? '已写入' : '预览';
  console.log(`${mode}: ${changedFiles.length} 篇文章匹配`);
  console.log(`分类: ${args.primary} / ${args.oldSecondary} -> ${args.primary} / ${args.newSecondary}`);

  for (const file of changedFiles) {
    console.log(`- ${path.relative(path.resolve(__dirname, '..'), file)}`);
  }

  if (!args.write && changedFiles.length > 0) {
    console.log('\n确认无误后执行: node scripts/rename-secondary-category.cjs --write');
  }
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`错误: ${error.message}`);
    console.error('执行 node scripts/rename-secondary-category.cjs --help 查看用法');
    process.exit(1);
  }
}
