/** Auth state. Only the identity lives here; server data lives in React Query. */
import { create } from 'zustand'
import { api, tokens } from '../lib/api'
import type { Tokens } from '../lib/types'

interface Me { id: number; email: string; is_demo: boolean; has_profile: boolean }

interface AuthState {
  me: Me | null
  status: 'unknown' | 'authenticated' | 'anonymous'
  error: string | null
  load: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
}

export const useAuth = create<AuthState>((set) => ({
  me: null,
  status: 'unknown',
  error: null,

  async load() {
    if (!tokens.access() && !tokens.refresh()) {
      set({ status: 'anonymous', me: null })
      return
    }
    try {
      set({ me: await api.get<Me>('/auth/me'), status: 'authenticated', error: null })
    } catch {
      tokens.clear()
      set({ status: 'anonymous', me: null })
    }
  },

  async login(email, password) {
    set({ error: null })
    try {
      tokens.save(await api.post<Tokens>('/auth/login', { email, password }))
      set({ me: await api.get<Me>('/auth/me'), status: 'authenticated' })
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Sign in failed' })
      throw e
    }
  },

  async register(email, password, displayName) {
    set({ error: null })
    try {
      tokens.save(await api.post<Tokens>('/auth/register', {
        email, password, display_name: displayName
      }))
      set({ me: await api.get<Me>('/auth/me'), status: 'authenticated' })
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Registration failed' })
      throw e
    }
  },

  logout() {
    tokens.clear()
    set({ me: null, status: 'anonymous' })
  }
}))
