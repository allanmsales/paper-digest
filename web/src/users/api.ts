import type { User } from './types'

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/users${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`
    throw new Error(detail)
  }

  return response.status === 204 ? (undefined as T) : response.json()
}

/** The signed-in user, or null when signed out. */
export async function me(): Promise<User | null> {
  const response = await fetch('/api/users/me')
  if (response.status === 401) return null
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

export function login(email: string, password: string): Promise<User> {
  return request('POST', '/login', { email, password })
}

export function logout(): Promise<void> {
  return request('POST', '/logout')
}

export function listUsers(): Promise<User[]> {
  return request('GET', '')
}

export function createUser(email: string, password: string, isAdmin: boolean): Promise<User> {
  return request('POST', '', { email, password, is_admin: isAdmin })
}

export function changePassword(userId: number, password: string): Promise<void> {
  return request('PUT', `/${userId}/password`, { password })
}

export function deleteUser(userId: number): Promise<void> {
  return request('DELETE', `/${userId}`)
}
