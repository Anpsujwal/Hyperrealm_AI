import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
const CURRENT_YEAR = new Date().getFullYear()

export function LoginPage() {
  const { login } = useAuth()
  const { resolvedTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await login(email, password)
      navigate('/app/dashboard')
    } catch (err: any) {
      setError(err?.message || 'Invalid email or password. Please try again.')
    } finally {
      setIsSubmitting(false)
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
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-gradient-to-br from-indigo-50/90 via-violet-50/60 to-[var(--bg-base)] dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950 border-r border-[var(--border-default)] dark:border-zinc-800">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(99,102,241,0.12)_0%,transparent_60%)] dark:hidden pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[400px] bg-violet-400/10 dark:hidden blur-[120px] pointer-events-none" />

        <Link to="/" className="relative flex items-center gap-2.5 w-fit">
          <div className="h-9 w-9 rounded-xl overflow-hidden border border-cyan-500/40 shadow-[0_0_16px_rgba(6,182,212,0.35)] flex items-center justify-center bg-zinc-950 flex-shrink-0">
            <img src="/hyperrealm-logo.jpg" alt="HYPERREALM" className="h-full w-full object-cover scale-110" />
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
          <Link to="/" className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="h-8 w-8 rounded-lg overflow-hidden border border-cyan-500/30 shadow-xs flex items-center justify-center bg-zinc-950 flex-shrink-0">
              <img src="/hyperrealm-logo.jpg" alt="HYPERREALM" className="h-full w-full object-cover scale-110" />
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
              loading={isSubmitting}
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
                onClick={() => selectPersona('ayesha.hussain@hyperrealm.io')}
                className="p-2.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors cursor-pointer group"
              >
                <div className="font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-indigo)]">Ayesha Hussain</div>
                <div className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">Admin / CTO</div>
                <div className="text-[10px] text-[var(--text-muted)] truncate">ayesha.hussain@hyperrealm.io</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('bob.harris@hyperrealm.io')}
                className="p-2.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors cursor-pointer group"
              >
                <div className="font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-indigo)]">Bob Harris</div>
                <div className="text-[10px] font-semibold text-cyan-700 dark:text-cyan-400">Tech Lead</div>
                <div className="text-[10px] text-[var(--text-muted)] truncate">bob.harris@hyperrealm.io</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('eve.russo@hyperrealm.io')}
                className="p-2.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors cursor-pointer group"
              >
                <div className="font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-indigo)]">Eve Russo</div>
                <div className="text-[10px] font-semibold text-amber-700 dark:text-amber-400">QA Engineer</div>
                <div className="text-[10px] text-[var(--text-muted)] truncate">eve.russo@hyperrealm.io</div>
              </button>
              <button
                type="button"
                onClick={() => selectPersona('henry.park@hyperrealm.io')}
                className="p-2.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-left transition-colors cursor-pointer group"
              >
                <div className="font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-indigo)]">Henry Park</div>
                <div className="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400">Project Manager</div>
                <div className="text-[10px] text-[var(--text-muted)] truncate">henry.park@hyperrealm.io</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
