import { contentHref, resolveContentUrl } from '../composables/contentPaths.ts';

export function withPublicBase(value: string, base: string) {
  if (!value.startsWith('/') || value.startsWith('//')) return value;
  return base.replace(/\/$/, '') + value;
}

export function publicPageHref(route: string, base: string) {
  return withPublicBase(contentHref(route === '/' ? route : route + '/'), base);
}

export function resolvePublicMarkdownLink(
  value: string,
  relativePath: string,
  assets: Record<string, string>,
  base: string,
) {
  const local = resolveContentUrl(value, relativePath, {});
  if (local.startsWith('/')) return withPublicBase(local, base);
  return resolveContentUrl(value, relativePath, assets);
}

export function headingAnchor(text: string, used: Set<string>) {
  const base = text.trim().toLowerCase().replace(/[^\p{L}\p{N}\p{M}\s_-]/gu, '').replace(/\s/g, '-') || 'section';
  let id = base;
  let index = 1;
  while (used.has(id)) id = `${base}-${index++}`;
  used.add(id);
  return id;
}
