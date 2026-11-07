import type { ContentManifest } from '../../src/types/content';

export function writeStaticPages(options: {
  outDir: string;
  manifest: Pick<ContentManifest, 'tree' | 'tags'>;
}): number;
