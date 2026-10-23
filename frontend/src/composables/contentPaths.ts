export function contentPath(root: string, segments: string | string[] = []) {
  const parts = Array.isArray(segments) ? segments : [segments];
  return [root, ...parts.filter(Boolean)].join('/');
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
