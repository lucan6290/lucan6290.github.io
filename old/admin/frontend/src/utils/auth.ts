interface AuthSession {
  accessToken: string
  username: string
  expiresAt: number
}

const AUTH_STORAGE_KEY = 'luchuan_admin_session'

function readStoredSession(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
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

export function setAuthSession(session: AuthSession): void {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function getAuthSession(): AuthSession | null {
  return readStoredSession()
}

export function getAuthToken(): string | null {
  return readStoredSession()?.accessToken || null
}

export function clearAuthSession(): void {
  window.localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function isAuthenticated(): boolean {
  return Boolean(readStoredSession())
}
