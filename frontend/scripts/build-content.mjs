#!/usr/bin/env node
/**
 * 自研内容管线：扫描 frontend/content/ → 生成 manifest / search-index / tags / archive。
 * dev 模式由 Vite 插件调用（带 chokidar 增量），生产构建由 pnpm prebuild 触发。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const CONTENT_DIR = path.join(ROOT, 'content');
const OUT_DIR = path.join(ROOT, 'src', 'generated');

const MD_EXT = /\.(md|mdx)$/i;
const NUMERIC_PREFIX = /^(\d+)[-_]/;
const EXCERPT_MAX = 180;

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function parseSortKey(name) {
  const m = name.match(NUMERIC_PREFIX);
  return m ? m[1].padStart(6, '0') : null;
}

function stripPrefix(name) {
  return name.replace(NUMERIC_PREFIX, '');
}

function excerptFromContent(content) {
  const text = content
    .replace(/^---[\s\S]*?---/, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/[#*>`~\[\]!_\-]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return text.length > EXCERPT_MAX ? text.slice(0, EXCERPT_MAX) + '…' : text;
}

function walkTree(dir, basePath, relativeRoot) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const nodes = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name.startsWith('_')) continue;
    const fullPath = path.join(dir, entry.name);
    const rel = path.relative(relativeRoot, fullPath).replace(/\\/g, '/');
    const urlPath = '/' + rel.replace(MD_EXT, '');

    if (entry.isDirectory()) {
      const children = walkTree(fullPath, urlPath, relativeRoot);
      const label = stripPrefix(entry.name);
      nodes.push({
        name: entry.name,
        label,
        path: urlPath,
        sortKey: parseSortKey(entry.name),
        children,
      });
    } else if (MD_EXT.test(entry.name)) {
      const raw = fs.readFileSync(fullPath, 'utf-8');
      const parsed = matter(raw);
      const fm = parsed.data || {};
      const stat = fs.statSync(fullPath);
      const slug = path.basename(entry.name, path.extname(entry.name));
      const article = {
        slug,
        path: basePath.endsWith(slug) ? basePath : urlPath,
        relativePath: rel,
        frontmatter: {
          title: fm.title || stripPrefix(slug),
          date: fm.date ? String(fm.date) : stat.birthtime.toISOString(),
          updated: fm.updated ? String(fm.updated) : stat.mtime.toISOString(),
          tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
          description: fm.description || '',
          sticky: Boolean(fm.sticky),
        },
        sortKey: parseSortKey(entry.name),
        mtimeMs: stat.mtimeMs,
        excerpt: fm.description || excerptFromContent(parsed.content),
      };
      nodes.push({
        name: entry.name,
        label: article.frontmatter.title,
        path: article.path,
        sortKey: article.sortKey,
        children: [],
        article,
      });
    }
  }

  nodes.sort((a, b) => {
    // 目录在前，文章在后；同类型按 sortKey → name
    if (Boolean(a.article) !== Boolean(b.article)) return a.article ? 1 : -1;
    if (a.sortKey && b.sortKey) return a.sortKey.localeCompare(b.sortKey);
    if (a.sortKey) return -1;
    if (b.sortKey) return 1;
    return a.name.localeCompare(b.name);
  });
  return nodes;
}

function flattenArticles(nodes, acc = {}) {
  for (const n of nodes) {
    if (n.article) acc[n.article.path] = n.article;
    if (n.children.length) flattenArticles(n.children, acc);
  }
  return acc;
}

function buildPrevNext(articles) {
  // 同父目录下按当前排序衔接
  const byParent = new Map();
  for (const art of Object.values(articles)) {
    const parent = art.path.split('/').slice(0, -1).join('/') || '/';
    if (!byParent.has(parent)) byParent.set(parent, []);
    byParent.get(parent).push(art);
  }

  const result = {};
  for (const list of byParent.values()) {
    list.sort((a, b) => {
      if (a.frontmatter.sticky !== b.frontmatter.sticky) return a.frontmatter.sticky ? -1 : 1;
      if (a.sortKey && b.sortKey) return a.sortKey.localeCompare(b.sortKey);
      if (a.sortKey) return -1;
      if (b.sortKey) return 1;
      return new Date(a.frontmatter.date).getTime() - new Date(b.frontmatter.date).getTime();
    });
    for (let i = 0; i < list.length; i++) {
      const pick = (idx) =>
        idx >= 0 && idx < list.length
          ? { slug: list[idx].slug, path: list[idx].path, title: list[idx].frontmatter.title }
          : null;
      result[list[i].path] = { prev: pick(i - 1), next: pick(i + 1) };
    }
  }
  return result;
}

function buildTags(articles) {
  const map = {};
  for (const art of Object.values(articles)) {
    for (const tag of art.frontmatter.tags || []) {
      if (!map[tag]) map[tag] = [];
      map[tag].push(art.path);
    }
  }
  return map;
}

function buildArchive(articles) {
  const tree = {};
  for (const art of Object.values(articles)) {
    const d = new Date(art.frontmatter.date);
    if (Number.isNaN(d.getTime())) continue;
    const y = String(d.getFullYear());
    const m = String(d.getMonth() + 1).padStart(2, '0');
    if (!tree[y]) tree[y] = {};
    if (!tree[y][m]) tree[y][m] = [];
    tree[y][m].push(art.path);
  }
  // 月份内按日期倒序
  for (const months of Object.values(tree)) {
    for (const paths of Object.values(months)) {
      paths.sort((a, b) => {
        const da = new Date(articles[a].frontmatter.date).getTime();
        const db = new Date(articles[b].frontmatter.date).getTime();
        return db - da;
      });
    }
  }
  return tree;
}

function buildRecent(articles, limit = 10) {
  return Object.values(articles)
    .sort((a, b) => {
      const ua = new Date(a.frontmatter.updated || a.frontmatter.date).getTime();
      const ub = new Date(b.frontmatter.updated || b.frontmatter.date).getTime();
      return ub - ua;
    })
    .slice(0, limit)
    .map((a) => a.path);
}

function buildSearchIndex(articles) {
  // minisearch 兼容的文档数组；运行时由 useSearch 加载并实例化 MiniSearch
  return Object.values(articles).map((a) => ({
    id: a.path,
    title: a.frontmatter.title,
    description: a.frontmatter.description || a.excerpt,
    tags: (a.frontmatter.tags || []).join(' '),
    path: a.path,
  }));
}

export function build() {
  ensureDir(OUT_DIR);
  if (!fs.existsSync(CONTENT_DIR)) {
    fs.mkdirSync(CONTENT_DIR, { recursive: true });
  }

  const tree = walkTree(CONTENT_DIR, '/', CONTENT_DIR);
  const articles = flattenArticles(tree);
  const prevNext = buildPrevNext(articles);
  const tags = buildTags(articles);
  const archive = buildArchive(articles);
  const recent = buildRecent(articles);
  const searchDocs = buildSearchIndex(articles);

  fs.writeFileSync(path.join(OUT_DIR, 'content-manifest.json'), JSON.stringify({ tree, articles, prevNext, tags, archive, recent }, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'search-index.json'), JSON.stringify(searchDocs, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'tags.json'), JSON.stringify(tags, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'archive.json'), JSON.stringify(archive, null, 2));

  console.log(`[build-content] ${Object.keys(articles).length} articles, ${Object.keys(tags).length} tags, ${recent.length} recent.`);
  return { tree, articles, prevNext, tags, archive, recent, searchDocs };
}

// 直接执行
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  build();
}
