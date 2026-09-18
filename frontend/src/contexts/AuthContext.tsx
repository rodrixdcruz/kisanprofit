import { createContext, useContext, useState, ReactNode } from 'react'
import { api } from '../lib/api'
import type { Token, User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  login: (mobile: string, password: string) => Promise<void>
  register: (name: string, mobile: string, password: string, language?: string) => Promise<void>
  logout: () => void
  demoLogin: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)

  const applyToken = (t: Token) => {
    localStorage.setItem('kp_token', t.access_token)
    setToken(t.access_token)
    setUser(t.user)
  }

  const login = async (mobile: string, password: string) => {
    applyToken(await api.post<Token>('/auth/login', { mobile, password }))
  }
  const register = async (name: string, mobile: string, password: string, language = 'en') => {
    applyToken(await api.post<Token>('/auth/register', { name, mobile, password, language }))
  }
  const demoLogin = async () => {
    applyToken(await api.post<Token>('/auth/login', { mobile: '9999999999', password: 'demo1234' }))
  }
  const logout = () => {
    localStorage.removeItem('kp_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, demoLogin }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
