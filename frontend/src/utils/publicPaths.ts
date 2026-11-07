import { contentHref, withBasePath } from '../composables/contentPaths.ts';

export { withBasePath as withPublicBase, resolveContentUrl as resolvePublicMarkdownLink } from '../composables/contentPaths.ts';

export function publicPageHref(route: string, base: string) {
  return withBasePath(contentHref(route === '/' ? route : route + '/'), base);
}

export function headingAnchor(text: string, used: Set<string>) {
  const base = text.trim().toLowerCase().replace(/[^\p{L}\p{N}\p{M}\s_-]/gu, '').replace(/\s/g, '-') || 'section';
  let id = base;
  let index = 1;
  while (used.has(id)) id = `${base}-${index++}`;
  used.add(id);
  return id;
}
