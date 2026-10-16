import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn, getInitials } from '@/lib/utils'

interface AvatarProps {
  src?: string
  name?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  statusDot?: 'online' | 'away' | 'busy' | 'offline'
}

const sizes = {
  xs: 'h-6 w-6 text-xs',
  sm: 'h-8 w-8 text-xs',
  md: 'h-9 w-9 text-sm',
  lg: 'h-11 w-11 text-base',
  xl: 'h-14 w-14 text-lg',
}

const dotSizes = {
  xs: 'h-1.5 w-1.5 -right-0 -bottom-0',
  sm: 'h-2 w-2 right-0 bottom-0',
  md: 'h-2.5 w-2.5 right-0 bottom-0',
  lg: 'h-3 w-3 right-0.5 bottom-0.5',
  xl: 'h-3.5 w-3.5 right-0.5 bottom-0.5',
}

const dotColors = {
  online: 'bg-emerald-400',
  away: 'bg-amber-400',
  busy: 'bg-rose-400',
  offline: 'bg-[var(--text-muted)]',
}

export function Avatar({ src, name = '', size = 'md', className, statusDot }: AvatarProps) {
  return (
    <div className="relative inline-flex flex-shrink-0">
      <AvatarPrimitive.Root
        className={cn(
          'relative flex items-center justify-center overflow-hidden rounded-full bg-[var(--bg-overlay)] border border-[var(--border-default)] select-none',
          sizes[size],
          className
        )}
      >
        {src && (
          <AvatarPrimitive.Image
            src={src}
            alt={name}
            className="h-full w-full object-cover"
          />
        )}
        <AvatarPrimitive.Fallback
          className="flex items-center justify-center h-full w-full font-semibold text-[var(--accent-indigo)]"
          delayMs={300}
        >
          {getInitials(name) || '?'}
        </AvatarPrimitive.Fallback>
      </AvatarPrimitive.Root>

      {statusDot && (
        <span
          className={cn(
            'absolute rounded-full border-2 border-[var(--bg-base)]',
            dotSizes[size],
            dotColors[statusDot]
          )}
        />
      )}
    </div>
  )
}
