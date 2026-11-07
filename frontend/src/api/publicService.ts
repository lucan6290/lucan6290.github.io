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
