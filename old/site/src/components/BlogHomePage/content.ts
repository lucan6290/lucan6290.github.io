import {usePluginData} from '@docusaurus/useGlobalData';

export type BlogSummary = {
  title: string;
  description: string;
  permalink: string;
  date: string;
  readingTime?: number;
  tags: string[];
  category: string;
  categoryPath: string;
};

export function useBlogSummaries(): BlogSummary[] {
  const data = usePluginData('blog-category-pages') as {posts?: BlogSummary[]} | undefined;
  return data?.posts ?? [];
}

export function formatPostDate(date: string): string {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return '';
  }
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai',
  }).format(parsed).replace(/\//g, '.');
}
