import { type HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'rounded-[var(--radius-lg)] border transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-[var(--bg-surface)] border-[var(--border-default)]',
        elevated: 'bg-[var(--bg-elevated)] border-[var(--border-default)]',
        overlay: 'bg-[var(--bg-overlay)] border-[var(--border-strong)]',
        glass: 'glass',
        gemini: 'bg-[var(--bg-surface)] border-[var(--border-default)] shadow-[0_4px_24px_-4px_rgba(155,114,207,0.1)] hover:border-purple-500/35 hover:shadow-[0_8px_32px_-4px_rgba(155,114,207,0.22)]',
        ghost: 'border-transparent bg-transparent',
      },
      interactive: {
        true: 'cursor-pointer hover:border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] hover:shadow-[var(--shadow-md)]',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      interactive: false,
    },
  }
)

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, interactive, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, interactive }), className)}
      {...props}
    />
  )
)
Card.displayName = 'Card'

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col gap-1.5 p-5 pb-0', className)}
      {...props}
    />
  )
)
CardHeader.displayName = 'CardHeader'

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-base font-semibold text-[var(--text-primary)] leading-none', className)}
      {...props}
    />
  )
)
CardTitle.displayName = 'CardTitle'

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-[var(--text-secondary)]', className)}
      {...props}
    />
  )
)
CardDescription.displayName = 'CardDescription'

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-5', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center p-5 pt-0', className)}
      {...props}
    />
  )
)
CardFooter.displayName = 'CardFooter'
