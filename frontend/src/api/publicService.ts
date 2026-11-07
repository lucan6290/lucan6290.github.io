function configuredUrl(value: string | undefined) {
  if (!value) return null;
  try {
    const url = new URL(value);
    const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
    if (url.username || url.password || url.search || url.hash) return null;
    if (url.protocol !== 'https:' && !(local && url.protocol === 'http:')) return null;
    return url.href.replace(/\/+$/, '') + '/api/v1';
  } catch {
    return null;
  }
}

const base = configuredUrl(import.meta.env.VITE_PUBLIC_SERVICE_URL);
export const publicServiceConfigured = base !== null;

export type PublicComment = {
  id: number;
  body: string;
  created_at: string;
};

type CommentPage<T> = { comments: T[]; next_before: number | null };
type ArticleResponse = CommentPage<PublicComment> & { views: number };

export class PublicServiceError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  { body, method = 'GET', token, signal }: { body?: object; method?: string; token?: string; signal?: AbortSignal } = {},
): Promise<T> {
  if (!base) throw new PublicServiceError(503, 'service_disabled', '站点尚未配置互动服务');
  const headers = new Headers({ Accept: 'application/json' });
  if (body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const timeout = AbortSignal.timeout(8000);
  const response = await fetch(base + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'omit',
    cache: 'no-store',
    redirect: 'error',
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const code = typeof error?.code === 'string' ? error.code : 'request_failed';
    const message = typeof error?.message === 'string' ? error.message : '请求失败，请稍后重试';
    throw new PublicServiceError(response.status, code, message);
  }
  return response.json();
}

function query(values: Record<string, string>, before?: number) {
  const params = new URLSearchParams(values);
  if (before !== undefined) params.set('before', String(before));
  return params.toString();
}

export function visitorSession() {
  const key = 'xiaocancoding:reading-session';
  try {
    const existing = sessionStorage.getItem(key);
    if (existing && /^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i.test(existing)) return existing;
    const session = crypto.randomUUID();
    sessionStorage.setItem(key, session);
    return session;
  } catch {
    return null;
  }
}

export const articleService = {
  get(articlePath: string, signal: AbortSignal, before?: number) {
    return request<ArticleResponse>(`/article?${query({ article_path: articlePath }, before)}`, { signal });
  },
  view(articlePath: string, sessionId: string, signal: AbortSignal) {
    return request<{ views: number }>('/views', {
      method: 'POST', body: { article_path: articlePath, session_id: sessionId }, signal,
    });
  },
  comment(articlePath: string, body: string, submissionId: string, signal: AbortSignal) {
    return request<{ status: 'accepted' }>('/comments', {
      method: 'POST', body: { article_path: articlePath, body, submission_id: submissionId }, signal,
    });
  },
};

export type CommentStatus = 'pending' | 'published' | 'rejected';
export type AdminComment = PublicComment & { article_path: string; status: CommentStatus };
export type DocumentSummary = { relative_path: string; title: string };
export type AuthorDocument = DocumentSummary & { raw_content: string; version: string };
type DocumentListing = { documents: DocumentSummary[]; directories: { relative_path: string; label: string }[] };

export const authorService = {
  session(token: string, signal: AbortSignal) {
    return request<{ writing_enabled: boolean }>('/admin/session', { token, signal });
  },
  documents(token: string, signal: AbortSignal) {
    return request<DocumentListing>('/admin/documents', { token, signal });
  },
  open(token: string, path: string, signal: AbortSignal) {
    return request<AuthorDocument>(`/admin/document?${query({ relative_path: path })}`, { token, signal });
  },
  save(token: string, path: string, raw: string, version: string | null, signal: AbortSignal) {
    const body = { relative_path: path, raw_content: raw };
    return version === null
      ? request<AuthorDocument>('/admin/documents', { method: 'POST', body, token, signal })
      : request<AuthorDocument>('/admin/document', {
        method: 'PUT', body: { ...body, expected_version: version }, token, signal,
      });
  },
  comments(token: string, status: CommentStatus, signal: AbortSignal, before?: number) {
    return request<CommentPage<AdminComment>>(`/admin/comments?${query({ status }, before)}`, { token, signal });
  },
  moderate(token: string, id: number, status: 'published' | 'rejected', signal: AbortSignal) {
    return request<AdminComment>(`/admin/comments/${id}`, { method: 'PATCH', body: { status }, token, signal });
  },
};
