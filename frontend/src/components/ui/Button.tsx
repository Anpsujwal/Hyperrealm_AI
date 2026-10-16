import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium',
    'transition-all duration-200 cursor-pointer select-none',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-indigo)] focus-visible:ring-offset-1 focus-visible:ring-offset-[var(--bg-base)]',
    'disabled:pointer-events-none disabled:opacity-40',
    'active:scale-[0.98]',
  ],
  {
    variants: {
      variant: {
        primary: [
          'bg-[var(--accent-indigo)] text-white',
          'hover:bg-[var(--accent-indigo-hover)] hover:shadow-[0_0_20px_rgba(99,102,241,0.35)]',
        ],
        secondary: [
          'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-default)]',
          'hover:bg-[var(--bg-overlay)] hover:border-[var(--border-strong)]',
        ],
        ghost: [
          'text-[var(--text-secondary)]',
          'hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]',
        ],
        outline: [
          'border border-[var(--accent-indigo)] text-[var(--accent-indigo)] bg-transparent',
          'hover:bg-[var(--accent-indigo)] hover:text-white',
        ],
        gemini: [
          'bg-gradient-to-r from-[#4285f4] via-[#9b72cf] to-[#d96570] text-white font-medium shadow-md',
          'hover:opacity-95 hover:shadow-[0_0_24px_rgba(155,114,207,0.4)] hover:scale-[1.01] active:scale-[0.98]',
        ],
        destructive: [
          'bg-[var(--accent-rose)] text-white',
          'hover:opacity-90',
        ],
        link: [
          'text-[var(--accent-indigo)] underline-offset-4 hover:underline p-0 h-auto',
        ],
      },
      size: {
        xs: 'h-7 px-2.5 text-xs rounded-md',
        sm: 'h-8 px-3 text-sm rounded-lg',
        md: 'h-9 px-4 text-sm rounded-lg',
        lg: 'h-11 px-6 text-base rounded-xl',
        icon: 'h-9 w-9 rounded-lg',
        'icon-sm': 'h-7 w-7 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'

export { buttonVariants }
