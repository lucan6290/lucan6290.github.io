import { statSync } from 'node:fs';
import path from 'node:path';
import type { Plugin } from 'vite';
import { contentHref } from '../composables/contentPaths.ts';

const IDENTITY_PATH = '/__luchuan_desktop_site';
const MARKDOWN = /\.(md|mdx)$/i;

export function sitePreviewRoute(contentRoot: string, documentPath: string | null) {
  if (documentPath === null) return '/';
  const parts = documentPath.split('/');
  const name = parts.at(-1) ?? '';
  const directories = parts.slice(0, -1);
  if (!MARKDOWN.test(name) || parts.some((part) => !part || /^[._]/.test(part) || /[\\:\x00-\x1f]/.test(part))
    || directories.some((part) => /^(images|assets|.*-imgs)$/i.test(part))) return null;
  try {
    if (!statSync(path.join(contentRoot, ...parts), { throwIfNoEntry: false })?.isFile()) return null;
  } catch {
    return null;
  }

  if (/^readme\.md$/i.test(name)) return contentHref('/' + directories.join('/'));
  return directories.length ? contentHref('/' + documentPath.replace(MARKDOWN, '')) : null;
}

/** 私有开发探针，用于桌面应用核对本地 Vite 进程和内容路径。 */
export function desktopSitePlugin(): Plugin {
  return {
    name: 'luchuan-desktop-site',
    configureServer(server) {
      const projectRoot = path.dirname(server.config.root);
      const contentRoot = path.join(server.config.root, 'content');
      server.middlewares.use((request, response, next) => {
        const url = new URL(request.url ?? '/', 'http://127.0.0.1');
        if (url.pathname !== IDENTITY_PATH) return next();
        if (request.method !== 'GET' || request.headers['x-luchuan-desktop'] !== '1') {
          response.statusCode = 404;
          response.end();
          return;
        }
        response.setHeader('Content-Type', 'application/json; charset=utf-8');
        response.setHeader('Cache-Control', 'no-store');
        response.end(JSON.stringify({
          service: 'xiaocancoding-site',
          project_root: projectRoot,
          pid: process.pid,
          route: sitePreviewRoute(contentRoot, url.searchParams.get('document')),
        }));
      });
    },
  };
}
