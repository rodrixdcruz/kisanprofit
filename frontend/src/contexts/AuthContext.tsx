import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '../lib/api'
import type { Token, User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  /** True while the shared demo account is signed in — every write is blocked. */
  isReadOnly: boolean
  login: (mobile: string, password: string) => Promise<void>
  register: (name: string, mobile: string, password: string, language?: string) => Promise<void>
  logout: () => void
  demoLogin: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  // A token in localStorage survives reloads, so restore it — and the user it
  // belongs to — instead of bouncing the visitor back to the login screen.
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('kp_token'))

  const applyToken = (t: Token) => {
    localStorage.setItem('kp_token', t.access_token)
    setToken(t.access_token)
    setUser(t.user)
  }

  const logout = () => {
    localStorage.removeItem('kp_token')
    setToken(null)
    setUser(null)
  }

  const login = async (mobile: string, password: string) => {
    applyToken(await api.post<Token>('/auth/login', { mobile, password }))
  }
  const register = async (name: string, mobile: string, password: string, language = 'en') => {
    applyToken(await api.post<Token>('/auth/register', { name, mobile, password, language }))
  }
  // One-tap entry asks the API for a demo session instead of embedding the
  // demo credentials, so an operator can rotate that password without a
  // frontend rebuild. Rate limited server-side; 404s when the demo is closed.
  const demoLogin = async () => {
    applyToken(await api.post<Token>('/auth/demo-login'))
  }

  useEffect(() => {
    if (!token || user) return
    let cancelled = false
    api.get<User>('/auth/session')
      .then((u) => { if (!cancelled) setUser(u) })
      .catch(() => {
        if (cancelled) return
        localStorage.removeItem('kp_token')
        setToken(null)
      })
    return () => { cancelled = true }
  }, [token, user])

  return (
    <AuthContext.Provider value={{
      user, token, isReadOnly: !!user?.is_demo, login, register, logout, demoLogin,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
