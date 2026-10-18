import { type HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1 font-medium rounded-full border whitespace-nowrap transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-[var(--bg-overlay)] border-[var(--border-default)] text-[var(--text-secondary)]',
        indigo: 'bg-indigo-500/10 dark:bg-indigo-500/15 border-indigo-500/25 text-indigo-700 dark:text-indigo-300',
        violet: 'bg-violet-500/10 dark:bg-violet-500/15 border-violet-500/25 text-violet-700 dark:text-violet-300',
        cyan: 'bg-cyan-500/10 dark:bg-cyan-500/15 border-cyan-500/25 text-cyan-800 dark:text-cyan-300',
        emerald: 'bg-emerald-500/10 dark:bg-emerald-500/15 border-emerald-500/25 text-emerald-800 dark:text-emerald-300',
        amber: 'bg-amber-500/10 dark:bg-amber-500/15 border-amber-500/25 text-amber-800 dark:text-amber-300',
        rose: 'bg-rose-500/10 dark:bg-rose-500/15 border-rose-500/25 text-rose-700 dark:text-rose-300',
        gemini: 'bg-gradient-to-r from-blue-50/90 via-purple-50/80 to-rose-50/70 dark:bg-none dark:bg-zinc-800 border border-purple-200/90 dark:border-zinc-700 text-purple-700 dark:text-zinc-200 shadow-xs dark:shadow-none',
      },
      size: {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-xs px-2.5 py-1',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    />
  )
)
Badge.displayName = 'Badge'

// Numeric dot badge for nav items
export function DotBadge({ count }: { count: number }) {
  if (count <= 0) return null
  return (
    <span className="ml-auto flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-[var(--accent-indigo)] text-white text-[10px] font-bold leading-none">
      {count > 99 ? '99+' : count}
    </span>
  )
}
