import type { ContentManifest } from '../../src/types/content';

export function build(options?: { contentDir?: string; outDir?: string }): ContentManifest & {
  searchDocs: Array<{ id: string; title: string; description: string; tags: string; path: string; body: string }>;
};
