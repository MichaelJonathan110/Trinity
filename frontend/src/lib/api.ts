/**
 * Single API client. Attaches the access token, refreshes once on 401, and surfaces
 * the backend's own error messages so the UI never has to invent one.
 */
import type { Tokens } from './types'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api/v1'
const ACCESS_KEY = 'trinity.access'
const REFRESH_KEY = 'trinity.refresh'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export const tokens = {
  access: () => localStorage.getItem(ACCESS_KEY),
  refresh: () => localStorage.getItem(REFRESH_KEY),
  save(t: Tokens) {
    localStorage.setItem(ACCESS_KEY, t.access_token)
    localStorage.setItem(REFRESH_KEY, t.refresh_token)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }
}

async function refreshTokens(): Promise<boolean> {
  const rt = tokens.refresh()
  if (!rt) return false
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: rt })
  })
  if (!res.ok) { tokens.clear(); return false }
  tokens.save((await res.json()) as Tokens)
  return true
}

async function readError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      const first = data.detail[0] as { msg?: string }
      if (first?.msg) return first.msg
    }
  } catch { /* body was not JSON */ }
  return res.statusText || `Request failed (${res.status})`
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const at = tokens.access()
  if (at) headers.set('Authorization', `Bearer ${at}`)

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 401 && retry && (await refreshTokens())) {
    return request<T>(path, init, false)
  }
  if (!res.ok) throw new ApiError(res.status, await readError(res))
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/**
 * Multipart upload for progress photos. The browser must set the multipart
 * boundary itself, so this path deliberately does NOT set Content-Type - unlike
 * the JSON helpers above.
 */
async function upload<T>(path: string, form: FormData, retry = true): Promise<T> {
  const headers = new Headers()
  const at = tokens.access()
  if (at) headers.set('Authorization', `Bearer ${at}`)
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form, headers })
  if (res.status === 401 && retry && (await refreshTokens())) return upload<T>(path, form, false)
  if (!res.ok) throw new ApiError(res.status, await readError(res))
  return (await res.json()) as T
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  put: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T,>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload
}
