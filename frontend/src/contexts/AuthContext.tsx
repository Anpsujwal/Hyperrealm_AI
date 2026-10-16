import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import type { User } from '@/types'
import { authApi, getToken, clearToken } from '@/lib/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  signup: (name: string, email: string, password: string) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Restore session from token on initial load
  useEffect(() => {
    let mounted = true

    async function checkAuth() {
      const token = getToken()
      if (!token) {
        if (mounted) {
          setState({ user: null, isAuthenticated: false, isLoading: false })
        }
        return
      }

      try {
        const user = await authApi.getMe()
        if (mounted) {
          setState({ user, isAuthenticated: true, isLoading: false })
        }
      } catch {
        clearToken()
        if (mounted) {
          setState({ user: null, isAuthenticated: false, isLoading: false })
        }
      }
    }

    checkAuth()

    const handleUnauthorized = () => {
      setState({ user: null, isAuthenticated: false, isLoading: false })
    }

    window.addEventListener('hyperrealm:unauthorized', handleUnauthorized)
    return () => {
      mounted = false
      window.removeEventListener('hyperrealm:unauthorized', handleUnauthorized)
    }
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const user = await authApi.getMe()
      setState((s) => ({ ...s, user, isAuthenticated: true }))
    } catch {
      // ignore
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, isLoading: true }))
    try {
      const res = await authApi.login(email, password)
      setState({ user: res.user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      setState((s) => ({ ...s, isLoading: false }))
      throw err
    }
  }, [])

  const signup = useCallback(async (name: string, email: string, password: string) => {
    setState((s) => ({ ...s, isLoading: true }))
    try {
      const res = await authApi.signup(name, email, password)
      setState({ user: res.user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      setState((s) => ({ ...s, isLoading: false }))
      throw err
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore logout errors
    } finally {
      setState({ user: null, isAuthenticated: false, isLoading: false })
    }
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, logout, signup, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
