import { hasSeriesRoute } from '../../src/utils/seriesPaths.js';

export function parseSeries(value, source) {
  if (value === undefined) return undefined;
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${source} 的 series 必须包含 id、title 和 order。`);
  }
  const { id, title, order } = value;
  if (typeof id !== 'string' || id.length > 64 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) {
    throw new Error(`${source} 的 series.id 必须是最长 64 字符的小写英文、数字和连字符。`);
  }
  if (typeof title !== 'string' || !title.trim()) {
    throw new Error(`${source} 的 series.title 必须是非空字符串。`);
  }
  if (!Number.isSafeInteger(order) || order <= 0) {
    throw new Error(`${source} 的 series.order 必须是正整数。`);
  }
  return { id, title: title.trim(), order };
}

export function buildSeries(articles, tree) {
  const grouped = new Map();
  for (const article of Object.values(articles)) {
    const member = article.frontmatter.series;
    if (!member) continue;
    const { id, title, order } = member;
    const group = grouped.get(id) || { id, title, articles: new Map() };
    if (group.title !== title) {
      throw new Error(`${article.relativePath} 的 series.title 与系列 ${id} 的标题不一致。`);
    }
    if (group.articles.has(order)) {
      throw new Error(`${article.relativePath} 的 series.order ${order} 与 ${group.articles.get(order).relativePath} 重复。`);
    }
    group.articles.set(order, article);
    grouped.set(id, group);
  }
  if (grouped.size && !hasSeriesRoute(tree)) {
    throw new Error('content/series 栏目已占用 /series，启用系列专题前请调整栏目目录。');
  }
  return Object.fromEntries([...grouped.keys()].sort().map(id => {
    const group = grouped.get(id);
    const articlePaths = [...group.articles.keys()].sort((a, b) => a - b)
      .map(order => group.articles.get(order).path);
    return [id, { id, title: group.title, articlePaths }];
  }));
}
