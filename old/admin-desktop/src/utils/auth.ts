interface AuthSession {
  accessToken: string
  username: string
  expiresAt: number // 秒级时间戳
}

const AUTH_STORAGE_KEY = 'luchuan_admin_session'

function readStoredSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const session = JSON.parse(raw) as AuthSession
    if (!session.accessToken || !session.expiresAt || session.expiresAt * 1000 <= Date.now()) {
      clearAuthSession()
      return null
    }
    return session
  } catch {
    clearAuthSession()
    return null
  }
}

export function getAuthToken(): string | null {
  return readStoredSession()?.accessToken || null
}

export function setAuthSession(token: string, expiresAt: number, username: string) {
  const session: AuthSession = { accessToken: token, username, expiresAt }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function isAuthenticated(): boolean {
  return readStoredSession() !== null
}

export function getUsername(): string | null {
  return readStoredSession()?.username || null
}
