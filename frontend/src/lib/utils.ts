import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return formatDate(d)
}

export function truncate(str: string, maxLen: number): string {
  return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const IST_TIMEZONE = 'Asia/Kolkata'

/**
 * Formats a date/string into Indian Standard Time (IST) 12-hour time (e.g., "06:30 PM IST")
 */
export function formatISTTime(date: Date | string, showLabel = true): string {
  try {
    const d = typeof date === 'string' ? new Date(date) : date
    const formatted = d.toLocaleTimeString('en-IN', {
      timeZone: IST_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
    return showLabel ? `${formatted} IST` : formatted
  } catch {
    return String(date)
  }
}

/**
 * Formats a date/string into Indian Standard Time (IST) date (e.g., "Sun, Oct 18, 2026")
 */
export function formatISTDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  try {
    const d = typeof date === 'string' ? new Date(date) : date
    return d.toLocaleDateString('en-IN', {
      timeZone: IST_TIMEZONE,
      weekday: options?.weekday ?? 'short',
      month: options?.month ?? 'short',
      day: options?.day ?? 'numeric',
      year: options?.year ?? 'numeric',
    })
  } catch {
    return String(date)
  }
}

/**
 * Formats into full date and time in IST (e.g., "Sun, Oct 18, 2026 at 06:30 PM IST")
 */
export function formatISTDateTime(date: Date | string): string {
  return `${formatISTDate(date)} at ${formatISTTime(date, true)}`
}

/**
 * Converts any ISO or Date object into a YYYY-MM-DDTHH:mm string in IST for datetime-local input
 */
export function toISTInputValue(date: Date | string): string {
  try {
    const d = typeof date === 'string' ? new Date(date) : date
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: IST_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
    const parts = formatter.formatToParts(d)
    const getPart = (type: string) => parts.find((p) => p.type === type)?.value || '00'
    return `${getPart('year')}-${getPart('month')}-${getPart('day')}T${getPart('hour')}:${getPart('minute')}`
  } catch {
    return ''
  }
}

/**
 * Converts a datetime-local input string (YYYY-MM-DDTHH:mm) into an ISO string tagged with +05:30 IST
 */
export function fromISTInputValue(localInputStr: string): string {
  if (!localInputStr) return ''
  const withTz = `${localInputStr}:00+05:30`
  return new Date(withTz).toISOString()
}

