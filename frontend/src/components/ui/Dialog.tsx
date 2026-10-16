import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

export const Dialog = DialogPrimitive.Root
export const DialogTrigger = DialogPrimitive.Trigger
export const DialogPortal = DialogPrimitive.Portal
export const DialogClose = DialogPrimitive.Close

export function DialogOverlay({ className, ...props }: DialogPrimitive.DialogOverlayProps) {
  return (
    <DialogPrimitive.Overlay
      className={cn(
        'fixed inset-0 z-50 bg-black/60 backdrop-blur-sm',
        'data-[state=open]:animate-fade-in data-[state=closed]:opacity-0',
        'transition-opacity duration-200',
        className
      )}
      {...props}
    />
  )
}

interface DialogContentProps extends DialogPrimitive.DialogContentProps {
  showClose?: boolean
}

export function DialogContent({
  className,
  children,
  showClose = true,
  ...props
}: DialogContentProps) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        className={cn(
          'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
          'w-full max-w-lg rounded-[var(--radius-xl)] p-6',
          'bg-[var(--bg-elevated)] border border-[var(--border-strong)]',
          'shadow-[var(--shadow-lg)]',
          'data-[state=open]:animate-slide-up',
          'focus:outline-none',
          className
        )}
        {...props}
      >
        {children}
        {showClose && (
          <DialogClose className="absolute right-4 top-4 rounded-md p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-overlay)] transition-colors">
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogClose>
        )}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex flex-col gap-1.5 mb-5', className)} {...props} />
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center justify-end gap-3 mt-6', className)} {...props} />
  )
}

export function DialogTitle({ className, ...props }: DialogPrimitive.DialogTitleProps) {
  return (
    <DialogPrimitive.Title
      className={cn('text-lg font-semibold text-[var(--text-primary)]', className)}
      {...props}
    />
  )
}

export function DialogDescription({ className, ...props }: DialogPrimitive.DialogDescriptionProps) {
  return (
    <DialogPrimitive.Description
      className={cn('text-sm text-[var(--text-secondary)]', className)}
      {...props}
    />
  )
}
