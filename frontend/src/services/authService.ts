import api from './api'

export interface AuthUser {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
}

const TOKEN_KEY = 'auth_token'
const REFRESH_KEY = 'refresh_token'
const USER_KEY = 'auth_user'

export const authService = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  getUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as AuthUser
    } catch {
      return null
    }
  },

  async login(username: string, password: string): Promise<AuthUser> {
    const { data } = await api.post<{ access_token: string; refresh_token: string }>('/auth/login', {
      username,
      password,
    })
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_KEY, data.refresh_token)
    const me = await api.get<AuthUser>('/auth/me')
    localStorage.setItem(USER_KEY, JSON.stringify(me.data))
    return me.data
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  },

  async listUsers(): Promise<AuthUser[]> {
    const response = await api.get<AuthUser[]>('/auth/users')
    return response.data
  },
}

export default authService
