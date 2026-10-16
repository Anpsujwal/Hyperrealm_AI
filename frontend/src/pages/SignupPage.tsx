import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, User, Building2, Zap, CheckCircle2, Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'

const perks = [
  'Four specialist AI agents',
  'Enterprise knowledge search',
  'Role-based learning paths',
  'Team collaboration tools',
  'Incident investigation & audit',
]

const CURRENT_YEAR = new Date().getFullYear()

export function SignupPage() {
  const { signup, isLoading } = useAuth()
  const { resolvedTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    org: '',
    password: '',
    confirm: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Partial<typeof form & { api?: string }>>({})

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [field]: e.target.value }))
    if (errors[field] || errors.api) {
      setErrors((prev) => ({ ...prev, [field]: undefined, api: undefined }))
    }
  }

  const validate = () => {
    const e: Partial<typeof form & { api?: string }> = {}
    if (!form.name.trim()) e.name = 'Full name is required'
    if (!form.email.includes('@')) e.email = 'Valid email is required'
    if (form.password.length < 8) e.password = 'At least 8 characters'
    if (form.password !== form.confirm) e.confirm = 'Passwords do not match'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    try {
      await signup(form.name, form.email, form.password)
      navigate('/app/dashboard')
    } catch (err: any) {
      setErrors((prev) => ({
        ...prev,
        api: err?.message || 'Failed to create account. Please try again.',
      }))
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-gradient-to-br from-indigo-950/60 to-[var(--bg-base)] border-r border-[var(--border-default)]">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(139,92,246,0.15)_0%,transparent_60%)] pointer-events-none" />

        <Link to="/" className="relative flex items-center gap-2.5 w-fit">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-[var(--shadow-glow-indigo)]">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-wide">HYPERREALM</span>
        </Link>

        <div className="relative">
          <h2 className="text-3xl font-bold leading-snug mb-4">
            Set up your<br />
            <span className="text-gradient-indigo">AI workspace today.</span>
          </h2>
          <p className="text-sm text-[var(--text-secondary)] mb-10">
            Everything your enterprise needs in one AI-powered platform.
          </p>

          <div className="space-y-3">
            {perks.map((p) => (
              <div key={p} className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
                <CheckCircle2 className="h-4 w-4 text-[var(--accent-emerald)] flex-shrink-0" />
                {p}
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-[var(--text-muted)]">
          © {CURRENT_YEAR} HYPERREALM
        </p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-y-auto relative">
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

        <div className="w-full max-w-sm py-8">
          <Link to="/" className="lg:hidden flex items-center gap-2 mb-8">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold tracking-wide">HYPERREALM</span>
          </Link>

          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">Create your account</h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Get started with HYPERREALM in minutes
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              id="signup-name"
              label="Full Name"
              type="text"
              value={form.name}
              onChange={update('name')}
              placeholder="Alex Morgan"
              autoComplete="name"
              leftIcon={<User className="h-4 w-4" />}
              error={errors.name}
            />

            <Input
              id="signup-email"
              label="Work Email"
              type="email"
              value={form.email}
              onChange={update('email')}
              placeholder="you@company.com"
              autoComplete="email"
              leftIcon={<Mail className="h-4 w-4" />}
              error={errors.email}
            />

            <Input
              id="signup-org"
              label="Organisation (optional)"
              type="text"
              value={form.org}
              onChange={update('org')}
              placeholder="Acme Corp"
              leftIcon={<Building2 className="h-4 w-4" />}
            />

            <Input
              id="signup-password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={update('password')}
              placeholder="Min. 8 characters"
              autoComplete="new-password"
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
              error={errors.password}
            />

            <Input
              id="signup-confirm"
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              value={form.confirm}
              onChange={update('confirm')}
              placeholder="Re-enter password"
              autoComplete="new-password"
              leftIcon={<Lock className="h-4 w-4" />}
              error={errors.confirm}
            />

            {errors.api && (
              <p className="text-xs text-[var(--accent-rose)] text-center py-1 bg-rose-500/10 rounded-md border border-rose-500/20" role="alert">
                {errors.api}
              </p>
            )}

            <Button
              type="submit"
              size="lg"
              className="w-full"
              loading={isLoading}
              id="signup-submit"
            >
              Create Account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
            Already have an account?{' '}
            <Link to="/login" className="text-[var(--accent-indigo)] hover:underline font-medium">
              Sign in
            </Link>
          </p>

          <p className="mt-6 text-center text-xs text-[var(--text-muted)] opacity-60">
            Demo mode: registration creates a local session only
          </p>
        </div>
      </div>
    </div>
  )
}
