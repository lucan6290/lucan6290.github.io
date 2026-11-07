/**
 * 内容管线核心实现（纯 ESM，无 shebang）。
 * - Vite 插件 import 此模块以在 dev/build 时生成 manifest。
 * - CLI 入口见同目录 build-content.mjs。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';
import { getProcessor } from 'bytemd';
import { buildSeries, parseSeries } from './contentSeries.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const CONTENT_DIR = path.join(ROOT, 'content');
const OUT_DIR = path.join(ROOT, 'src', 'generated');

const MD_EXT = /\.(md|mdx)$/i;
const NUMERIC_PREFIX = /^(\d+)[-_]/;
const EXCERPT_MAX = 180;
const RESOURCE_DIR = /^(?:images|assets|.*-imgs)$/i;
const markdownProcessor = getProcessor({});

function firstHeading(content) {
  const withoutCode = content.replace(/^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?^ {0,3}\1[^\n]*$/gm, '');
  return withoutCode.match(/^ {0,3}#[\t ]+(.+)$/m)?.[1]?.replace(/[\t ]+#+[\t ]*$/, '').trim();
}

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

function countWords(content) {
  const nodes = [markdownProcessor.parse(content)];
  const parts = [];
  while (nodes.length) {
    const node = nodes.pop();
    if (node.type === 'text' || node.type === 'inlineCode') parts.push(node.value);
    else if (node.children) nodes.push(...node.children);
  }
  const text = parts.join(' ');
  const chineseCharacters = text.match(/\p{Script=Han}/gu)?.length ?? 0;
  const latinWords = text.match(/[A-Za-z0-9]+(?:[.'’-][A-Za-z0-9]+)*/g)?.length ?? 0;
  return chineseCharacters + latinWords;
}

function articleDate(value) {
  const date = value instanceof Date ? value.toISOString() : typeof value === 'string' ? value.trim() : '';
  return Number.isFinite(Date.parse(date)) ? date : '';
}

function walkTree(dir, relativeRoot) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const nodes = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name.startsWith('_')) continue;
    const fullPath = path.join(dir, entry.name);
    const rel = path.relative(relativeRoot, fullPath).replace(/\\/g, '/');
    const urlPath = '/' + rel.replace(MD_EXT, '');

    if (entry.isDirectory()) {
      if (RESOURCE_DIR.test(entry.name)) continue;
      const entries = walkTree(fullPath, relativeRoot);
      const introduction = entries.find((node) => /^readme\.md$/i.test(node.name))?.article;
      const children = entries.filter((node) => !/^readme\.md$/i.test(node.name));
      if (dir !== relativeRoot && !children.length && !introduction) {
        // 三个内容栏目的空分类也可导航；只有图片等资源的目录仍不生成分类。
        const emptyCategory = /^(knowledge|blog|projects)\//.test(rel)
          && fs.readdirSync(fullPath).every((name) => name.startsWith('.') || name.startsWith('_'));
        if (!emptyCategory) continue;
      }
      const label = stripPrefix(entry.name);
      nodes.push({
        name: entry.name,
        label,
        path: urlPath,
        sortKey: parseSortKey(entry.name),
        children,
        ...(introduction ? { introduction } : {}),
      });
    } else if (MD_EXT.test(entry.name)) {
      const raw = fs.readFileSync(fullPath, 'utf-8');
      const parsed = matter(raw);
      const fm = parsed.data || {};
      const stat = fs.statSync(fullPath);
      const slug = path.basename(entry.name, path.extname(entry.name));
      const rawBody = parsed.content;
      const wordCount = countWords(rawBody);
      const series = rel.includes('/') && !/^readme\.md$/i.test(entry.name)
        ? parseSeries(fm.series, rel)
        : undefined;
      const article = {
        slug,
        path: urlPath,
        relativePath: rel,
        frontmatter: {
          title: fm.title || firstHeading(rawBody) || stripPrefix(slug),
          date: articleDate(fm.date),
          updated: articleDate(fm.updated),
          tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
          description: fm.description || '',
          sticky: Boolean(fm.sticky),
          ...(series ? { series } : {}),
        },
        sortKey: parseSortKey(entry.name),
        mtimeMs: stat.mtimeMs,
        excerpt: fm.description || excerptFromContent(rawBody),
        rawContent: rawBody,
        wordCount,
        readingMinutes: Math.max(1, Math.ceil(wordCount / 300)),
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
      if (!a.frontmatter.date || !b.frontmatter.date) return Number(Boolean(b.frontmatter.date)) - Number(Boolean(a.frontmatter.date));
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
      const ua = Date.parse(a.frontmatter.updated || a.frontmatter.date) || 0;
      const ub = Date.parse(b.frontmatter.updated || b.frontmatter.date) || 0;
      return ub - ua;
    })
    .slice(0, limit)
    .map((a) => a.path);
}

function searchText(content) {
  return content
    // 同一次扫描先保留代码，再清理普通文本中的注释、链接地址和 HTML。
    .replace(/(`+)([\s\S]*?)\1|(~{3,})([\s\S]*?)\3|<!--[\s\S]*?-->|!\[([^\]]*)\]\([^)]*\)|\[([^\]]+)\]\([^)]*\)|<[^>]*>/g,
      (_match, ticks, code, tildes, tildeCode, alt, label) => {
        if (ticks) return ticks.length >= 3 ? code.replace(/^[^\n]*\n/, '') : code;
        if (tildes) return tildeCode.replace(/^[^\n]*\n/, '');
        return alt ?? label ?? ' ';
      })
    .replace(/[#*>`~\[\]!]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildSearchIndex(articles) {
  return Object.values(articles).map((a) => {
    const body = searchText(a.rawContent);
    const description = a.frontmatter.description ? searchText(a.frontmatter.description) : body;
    return {
      id: a.path,
      title: a.frontmatter.title,
      description: description.length > EXCERPT_MAX ? description.slice(0, EXCERPT_MAX) + '…' : description,
      tags: (a.frontmatter.tags || []).join(' '),
      path: a.path,
      body,
    };
  });
}

export function build({ contentDir = CONTENT_DIR, outDir = OUT_DIR } = {}) {
  ensureDir(outDir);
  if (!fs.existsSync(contentDir)) {
    fs.mkdirSync(contentDir, { recursive: true });
  }

  const tree = walkTree(contentDir, contentDir);
  const articles = flattenArticles(tree);
  const prevNext = buildPrevNext(articles);
  const tags = buildTags(articles);
  const archive = buildArchive(articles);
  const recent = buildRecent(articles);
  const series = buildSeries(articles, tree);
  const searchDocs = buildSearchIndex(articles);

  fs.writeFileSync(path.join(outDir, 'content-manifest.json'), JSON.stringify({ tree, articles, prevNext, tags, archive, recent, series }, null, 2));
  fs.writeFileSync(path.join(outDir, 'search-index.json'), JSON.stringify(searchDocs, null, 2));
  fs.writeFileSync(path.join(outDir, 'tags.json'), JSON.stringify(tags, null, 2));
  fs.writeFileSync(path.join(outDir, 'archive.json'), JSON.stringify(archive, null, 2));

  console.log(`[build-content] ${Object.keys(articles).length} articles, ${Object.keys(tags).length} tags, ${recent.length} recent.`);
  return { tree, articles, prevNext, tags, archive, recent, series, searchDocs };
}
