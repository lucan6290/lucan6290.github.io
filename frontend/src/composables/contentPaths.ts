export const CONTENT_ROUTE_PATH = '/:section/:pathMatch(.*)*';

export function contentHref(path: string) {
  return path.split('/').map(encodeURIComponent).join('/');
}

export function contentPath(root: string, segments: string | string[] = []) {
  const parts = Array.isArray(segments) ? segments : [segments];
  return [root, ...parts.filter(Boolean)].join('/');
}

export function sidebarNodes<T extends { path: string }>(nodes: T[], root: string, path: string): T[] {
  if (root !== '/knowledge') return nodes;
  const section = path.slice(root.length).split('/').filter(Boolean)[0];
  if (!section) return [];
  const selected = nodes.find((node) => node.path === `${root}/${section}`);
  return selected ? [selected] : [];
}

/** 以 Markdown 源文件为基准，保留中文、空格、查询参数和锚点。 */
export function resolveContentUrl(value: string, relativePath: string, assets: Record<string, string>) {
  if (!value || /^(?:[a-z][a-z\d+.-]*:|\/|#|\?)/i.test(value)) return value;
  const base = relativePath.split('/').map(encodeURIComponent).join('/');
  const url = new URL(value, `https://notes.invalid/__content__/${base}`);
  if (!url.pathname.startsWith('/__content__/')) return value;
  let target: string;
  try {
    target = decodeURIComponent(url.pathname.slice('/__content__/'.length));
  } catch {
    return value;
  }
  const suffix = url.search + url.hash;
  if (/\.(md|mdx)$/i.test(target)) {
    const route = target.replace(/(?:^|\/)readme\.md$/i, '').replace(/\.(md|mdx)$/i, '');
    return '/' + route.split('/').map(encodeURIComponent).join('/') + suffix;
  }
  return assets[target] ? assets[target] + suffix : value;
}
