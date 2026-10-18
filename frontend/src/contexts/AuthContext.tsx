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

  // Restore session from token on initial load, or initialize default demo session
  useEffect(() => {
    let mounted = true

    async function checkAuth() {
      const token = getToken()
      if (token) {
        try {
          const user = await authApi.getMe()
          if (mounted) {
            setState({ user, isAuthenticated: true, isLoading: false })
            return
          }
        } catch {
          clearToken()
        }
      }

      // If user is explicitly on /login or /signup, do not auto-authenticate demo session
      const pathname = typeof window !== 'undefined' ? window.location.pathname : ''
      if (pathname === '/login' || pathname === '/signup') {
        if (mounted) {
          setState({ user: null, isAuthenticated: false, isLoading: false })
        }
        return
      }

      // Auto-authenticate default demo session if no token or token expired
      try {
        const res = await authApi.login('ayesha.hussain@hyperrealm.io', 'Password123!')
        if (mounted) {
          setState({ user: res.user, isAuthenticated: true, isLoading: false })
          return
        }
      } catch (err) {
        console.warn('Backend unavailable, using default local session:', err)
        if (mounted) {
          setState({
            user: {
              id: 'usr_alice',
              email: 'ayesha.hussain@hyperrealm.io',
              name: 'Ayesha Hussain',
              role: 'admin',
              department_id: 'dept_engineering',
              department_name: 'Engineering',
              created_at: new Date().toISOString(),
            },
            isAuthenticated: true,
            isLoading: false,
          })
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
