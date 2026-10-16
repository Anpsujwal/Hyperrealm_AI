import { type InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, leftIcon, rightIcon, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[var(--text-secondary)]"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full h-10.5 rounded-xl px-3.5',
              'bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-xs',
              'text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]',
              'transition-all duration-200',
              'hover:border-[var(--border-strong)]',
              'focus:outline-none focus:border-purple-500/60 focus:ring-2 focus:ring-purple-500/15 focus:shadow-[0_0_16px_rgba(155,114,207,0.15)]',
              error && 'border-[var(--accent-rose)] focus:border-[var(--accent-rose)] focus:ring-[var(--accent-rose)]',
              leftIcon && 'pl-9.5',
              rightIcon && 'pr-9.5',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">
              {rightIcon}
            </div>
          )}
        </div>
        {error && <p className="text-xs text-[var(--accent-rose)]">{error}</p>}
        {hint && !error && <p className="text-xs text-[var(--text-muted)]">{hint}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[var(--text-secondary)]">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'w-full rounded-xl px-3.5 py-3',
            'bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-xs',
            'text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]',
            'transition-all duration-200 resize-none',
            'hover:border-[var(--border-strong)]',
            'focus:outline-none focus:border-purple-500/60 focus:ring-2 focus:ring-purple-500/15 focus:shadow-[0_0_16px_rgba(155,114,207,0.15)]',
            error && 'border-[var(--accent-rose)]',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-[var(--accent-rose)]">{error}</p>}
        {hint && !error && <p className="text-xs text-[var(--text-muted)]">{hint}</p>}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'
