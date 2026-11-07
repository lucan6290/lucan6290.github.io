import type { ContentManifest } from '../../src/types/content';

export function writePublicPages(options: {
  outDir: string;
  manifest: ContentManifest;
  base: string;
  siteUrl?: string;
  assets?: Record<string, string>;
  warn?: (message: string) => void;
}): number;
