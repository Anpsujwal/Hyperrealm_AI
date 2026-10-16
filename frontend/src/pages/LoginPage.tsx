import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, Zap, ArrowRight, Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
const CURRENT_YEAR = new Date().getFullYear()

export function LoginPage() {
  const { login, isLoading } = useAuth()
  const { resolvedTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/app/dashboard')
    } catch (err: any) {
      setError(err?.message || 'Invalid email or password. Please try again.')
    }
  }

  const selectPersona = (pEmail: string) => {
    setEmail(pEmail)
    setPassword('Password123!')
    setError('')
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-gradient-to-br from-indigo-950/60 to-[var(--bg-base)] border-r border-[var(--border-default)]">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(99,102,241,0.18)_0%,transparent_60%)] pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[400px] bg-violet-600/8 blur-[120px] pointer-events-none" />

        <Link to="/" className="relative flex items-center gap-2.5 w-fit">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-[var(--shadow-glow-indigo)]">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-wide">HYPERREALM</span>
        </Link>

        <div className="relative">
          <h2 className="text-3xl font-bold leading-snug mb-4">
            Your AI command center<br />
            <span className="text-gradient-indigo">is waiting for you.</span>
          </h2>
          <p className="text-[var(--text-secondary)] text-sm leading-relaxed max-w-sm">
            Sign in to access your specialist agents, knowledge hub, and unified enterprise workspace.
          </p>

          <div className="mt-10 space-y-4">
            {['Knowledge Agent', 'Insights Agent', 'Collaborate Agent', 'Onboard Agent'].map(
              (agent, i) => (
                <div
                  key={agent}
                  className="flex items-center gap-3 text-sm text-[var(--text-secondary)]"
                  style={{ animationDelay: `${i * 0.1}s` }}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-indigo)]" />
                  {agent}
                </div>
              )
            )}
          </div>
        </div>

        <p className="relative text-xs text-[var(--text-muted)]">
          © {CURRENT_YEAR} HYPERREALM
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-6 relative">
        {/* Floating theme toggle */}
        <button
          onClick={toggleTheme}
          type="button"
          className="absolute top-6 right-6 p-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shadow-sm cursor-pointer"
          title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-indigo-500" />
          )}
        </button>

        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <Link to="/" className="lg:hidden flex items-center gap-2 mb-8">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold tracking-wide">HYPERREALM</span>
          </Link>

          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">Welcome back</h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Sign in to your HYPERREALM workspace
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              id="login-email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
              required
              leftIcon={<Mail className="h-4 w-4" />}
              error={error && !email ? 'Email is required' : undefined}
            />

            <Input
              id="login-password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
              leftIcon={<Lock className="h-4 w-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
            />

            {error && (
              <p className="text-xs text-[var(--accent-rose)] text-center" role="alert">
                {error}
              </p>
            )}

            <div className="flex justify-end">
              <a href="#" className="text-xs text-[var(--accent-indigo)] hover:underline">
                Forgot password?
              </a>
            </div>

            <Button
              type="submit"
              size="lg"
              className="w-full"
              loading={isLoading}
              id="login-submit"
            >
              Sign In
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
            Don't have an account?{' '}
            <Link to="/signup" className="text-[var(--accent-indigo)] hover:underline font-medium">
              Create account
            </Link>
          </p>

          <div className="mt-8 pt-6 border-t border-[var(--border-subtle)]">
            <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2.5 text-center">
              Quick demo login (password: Password123!)
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => selectPersona('alice.chen@hyperrealm.io')}
                className="p-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors"
              >
                <div className="font-medium text-[var(--text-primary)]">Alice Chen</div>
                <div className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">Admin / CTO</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('bob.harris@hyperrealm.io')}
                className="p-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors"
              >
                <div className="font-medium text-[var(--text-primary)]">Bob Harris</div>
                <div className="text-[10px] font-semibold text-cyan-700 dark:text-cyan-400">Tech Lead</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('eve.russo@hyperrealm.io')}
                className="p-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors"
              >
                <div className="font-medium text-[var(--text-primary)]">Eve Russo</div>
                <div className="text-[10px] font-semibold text-amber-700 dark:text-amber-400">QA Engineer</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('henry.park@hyperrealm.io')}
                className="p-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors"
              >
                <div className="font-medium text-[var(--text-primary)]">Henry Park</div>
                <div className="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400">Project Manager</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
