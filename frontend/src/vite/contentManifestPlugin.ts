import type { Plugin } from 'vite';
import { watch } from 'chokidar';
import path from 'node:path';
import { build } from '../../scripts/lib/buildContent.mjs';
import { writePublicPages } from '../../scripts/lib/publicPages.mjs';
import { writeStaticPages } from '../../scripts/lib/staticPages.mjs';
import { withPublicBase } from '../utils/publicPaths';

const VIRTUAL_ID = 'virtual:content-manifest';
const RESOLVED_ID = '\0' + VIRTUAL_ID;

/**
 * Vite 插件：将 content-manifest.json 暴露为虚拟模块，dev 模式下监听 content/ 变化并触发 HMR。
 */
export function contentManifestPlugin(): Plugin {
  let watcher: ReturnType<typeof watch> | null = null;
  let reloadTimer: ReturnType<typeof setTimeout> | null = null;
  let manifest: ReturnType<typeof build> | undefined;
  let base = '/';

  return {
    name: 'content-manifest',
    configResolved(config) {
      base = config.base;
    },
    resolveId(id) {
      if (id === VIRTUAL_ID) return RESOLVED_ID;
      return null;
    },
    load(id) {
      if (id === RESOLVED_ID) {
        manifest = build();
        const { tree, articles, prevNext, tags, archive, recent, series } = manifest;
        return `export default ${JSON.stringify({ tree, articles, prevNext, tags, archive, recent, series })};`;
      }
      return null;
    },
    writeBundle({ dir }, bundle) {
      if (!manifest || !dir) return;
      const assets: Record<string, string> = Object.create(null);
      for (const asset of Object.values(bundle)) {
        if (asset.type !== 'asset') continue;
        for (const source of asset.originalFileNames) {
          if (source.startsWith('content/')) {
            assets[source.slice('content/'.length)] = withPublicBase('/' + asset.fileName, base);
          }
        }
      }
      // Copy the untouched Vue shell first, then render public page bodies.
      writeStaticPages({ outDir: dir, manifest });
      const count = writePublicPages({ outDir: dir, manifest, base, assets, siteUrl: process.env.SITE_URL });
      console.log(`[public-pages] ${count} pages with static content.`);
    },
    configureServer(server) {
      const contentDir = path.resolve(process.cwd(), 'content');
      watcher = watch(contentDir, {
        ignoreInitial: true,
        ignored: ['**/node_modules/**', '**/.git/**'],
        awaitWriteFinish: { stabilityThreshold: 150, pollInterval: 50 },
      });
      const rebuild = () => {
        if (reloadTimer) clearTimeout(reloadTimer);
        reloadTimer = setTimeout(() => {
          const mod = server.moduleGraph.getModuleById(RESOLVED_ID);
          if (mod) {
            server.moduleGraph.invalidateModule(mod);
            server.ws.send({ type: 'full-reload' });
          }
        }, 100);
      };
      watcher.on('add', rebuild);
      watcher.on('change', rebuild);
      watcher.on('unlink', rebuild);
      watcher.on('addDir', rebuild);
      watcher.on('unlinkDir', rebuild);
      server.httpServer?.once('close', () => {
        if (reloadTimer) clearTimeout(reloadTimer);
        void watcher?.close();
      });
    },
    closeBundle() {
      if (reloadTimer) clearTimeout(reloadTimer);
      watcher?.close();
    },
  };
}
