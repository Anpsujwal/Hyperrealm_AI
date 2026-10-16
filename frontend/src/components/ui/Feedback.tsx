import { cn } from '@/lib/utils'

// ── Loading Spinner ──────────────────────────────────────────────────────────
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const spinnerSizes = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <svg
      className={cn('animate-spin text-[var(--accent-indigo)]', spinnerSizes[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading"
    >
      <circle
        className="opacity-20"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-80"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

// ── Full-page loading screen ─────────────────────────────────────────────────
export function PageLoader({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-4">
      <Spinner size="lg" />
      <p className="text-sm text-[var(--text-muted)] animate-pulse-subtle">{message}</p>
    </div>
  )
}

// ── Skeleton block ──────────────────────────────────────────────────────────
interface SkeletonProps {
  className?: string
  lines?: number
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('skeleton rounded-[var(--radius-md)]', className)}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard({ lines = 3 }: SkeletonProps) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-surface)] p-5 space-y-3">
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={cn('h-3', i === lines - 1 ? 'w-2/3' : 'w-full')} />
      ))}
    </div>
  )
}

// ── Typing indicator (for AI responses) ─────────────────────────────────────
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2" aria-label="AI is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-[var(--accent-indigo)] animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

// ── Empty state ──────────────────────────────────────────────────────────────
interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-4 py-16 text-center', className)}>
      {icon && (
        <div className="flex items-center justify-center h-16 w-16 rounded-[var(--radius-xl)] bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-muted)]">
          {icon}
        </div>
      )}
      <div className="space-y-1.5">
        <h3 className="text-base font-semibold text-[var(--text-primary)]">{title}</h3>
        {description && (
          <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto">{description}</p>
        )}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

// ── Error state ──────────────────────────────────────────────────────────────
interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-4 p-6 rounded-[var(--radius-lg)] border border-rose-500/20 bg-rose-500/5',
        className
      )}
    >
      <div className="h-10 w-10 rounded-full bg-rose-500/15 flex items-center justify-center">
        <svg
          className="h-5 w-5 text-rose-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <div className="text-center space-y-1">
        <p className="font-medium text-[var(--text-primary)]">{title}</p>
        <p className="text-sm text-[var(--text-secondary)]">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm text-[var(--accent-indigo)] hover:underline"
        >
          Try again
        </button>
      )}
    </div>
  )
}

// ── Inline notification ──────────────────────────────────────────────────────
type NotificationVariant = 'info' | 'success' | 'warning' | 'error'

interface NotificationProps {
  variant?: NotificationVariant
  title?: string
  message: string
  className?: string
}

const notifStyles: Record<NotificationVariant, string> = {
  info: 'border-indigo-500/30 bg-indigo-500/8 text-indigo-300',
  success: 'border-emerald-500/30 bg-emerald-500/8 text-emerald-300',
  warning: 'border-amber-500/30 bg-amber-500/8 text-amber-300',
  error: 'border-rose-500/30 bg-rose-500/8 text-rose-300',
}

export function Notification({
  variant = 'info',
  title,
  message,
  className,
}: NotificationProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex gap-3 rounded-[var(--radius-md)] border p-4 text-sm',
        notifStyles[variant],
        className
      )}
    >
      <div className="flex-1">
        {title && <p className="font-semibold mb-0.5">{title}</p>}
        <p className="opacity-80">{message}</p>
      </div>
    </div>
  )
}
