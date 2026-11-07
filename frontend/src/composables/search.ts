import MiniSearch from 'minisearch';

export interface SearchDocument {
  id: string;
  title: string;
  description: string;
  tags: string;
  path: string;
  body: string;
}

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  path: string;
}

function tokenize(text: string) {
  const terms: string[] = [];
  for (const part of text.normalize('NFKC').toLowerCase().match(/\p{Script=Han}+|[a-z0-9]+/gu) ?? []) {
    if (/\p{Script=Han}/u.test(part)) {
      const characters = Array.from(part);
      terms.push(...characters);
      // 相邻双字限制中文词序，避免“变量配置”误中分散的单字。
      for (let i = 1; i < characters.length; i++) terms.push(characters[i - 1] + characters[i]);
    } else {
      terms.push(part);
    }
  }
  return [...new Set(terms)];
}

export function createSearch(documents: SearchDocument[]) {
  const index = new MiniSearch<SearchDocument>({
    fields: ['title', 'tags', 'description', 'body'],
    storeFields: ['title', 'description', 'path'],
    tokenize,
    searchOptions: {
      combineWith: 'AND',
      prefix: (term) => /^[a-z0-9]/.test(term),
      boost: { title: 8, tags: 4, description: 2 },
    },
  });
  index.addAll(documents);
  return (query: string): SearchResult[] => {
    if (!query.trim()) return [];
    return index.search(query).slice(0, 30).map(({ id, title, description, path }) => ({ id, title, description, path }));
  };
}
