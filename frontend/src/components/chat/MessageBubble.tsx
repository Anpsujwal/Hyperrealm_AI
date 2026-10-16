import { useState } from 'react'
import { cn, formatRelativeTime, getInitials } from '@/lib/utils'
import { AGENTS } from '@/types'
import type { Message } from '@/types'
import { TypingIndicator } from '@/components/ui/Feedback'
import { Sparkles, Copy, Check } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface MessageBubbleProps {
  message: Message
}

const AGENT_COLORS: Record<string, string> = {
  auto: '#9b72cf',
  knowledge: '#4285f4',
  insights: '#9b72cf',
  collaborate: '#06b6d4',
  onboard: '#10b981',
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { user } = useAuth()
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const agent = message.agentId ? AGENTS.find((a) => a.id === message.agentId) : null
  const agentColor = message.agentId ? AGENT_COLORS[message.agentId] : '#9b72cf'

  const handleCopy = () => {
    if (!message.content) return
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div
      className={cn(
        'flex gap-3.5 animate-slide-up group/msg',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      {isUser ? (
        <div className="flex-shrink-0 h-8.5 w-8.5 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow-sm ring-2 ring-[var(--bg-surface)]">
          {getInitials(user?.name ?? 'You')}
        </div>
      ) : (
        <div
          className="flex-shrink-0 h-8.5 w-8.5 rounded-xl flex items-center justify-center shadow-xs border transition-transform duration-200"
          style={{
            backgroundColor: `${agentColor}18`,
            borderColor: `${agentColor}35`,
          }}
        >
          <Sparkles className="h-4 w-4" style={{ color: agentColor }} />
        </div>
      )}

      <div className={cn('flex flex-col gap-1.5 max-w-[80%]', isUser && 'items-end')}>
        {/* Agent label */}
        {!isUser && (
          <div className="flex items-center gap-2">
            <span
              className="text-xs font-semibold tracking-tight"
              style={{ color: agentColor }}
            >
              {agent?.name || 'Copilot AI'}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-muted)] font-medium">
              Gemini
            </span>
          </div>
        )}

        {/* Bubble */}
        <div
          className={cn(
            'px-5 py-3.5 text-sm leading-relaxed transition-all duration-200',
            isUser
              ? 'rounded-2xl rounded-tr-sm bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
              : 'rounded-2xl rounded-tl-sm bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-primary)] shadow-sm hover:border-[var(--border-strong)]'
          )}
        >
          {message.isStreaming ? (
            <TypingIndicator />
          ) : (
            <div className="whitespace-pre-wrap font-normal selection:bg-purple-500/20">{message.content}</div>
          )}
        </div>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {message.attachments.map((att) => (
              <div
                key={att.id}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] text-xs text-[var(--text-secondary)] shadow-xs"
              >
                <span className="text-purple-400">📎</span>
                <span>{att.name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Action toolbar & Timestamp */}
        <div className="flex items-center gap-3 px-1">
          <p className="text-[10px] text-[var(--text-muted)]">
            {formatRelativeTime(message.timestamp)}
          </p>

          {!isUser && !message.isStreaming && (
            <button
              onClick={handleCopy}
              className="opacity-0 group-hover/msg:opacity-100 flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all cursor-pointer"
              title="Copy response"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-500" />
                  <span className="text-emerald-500 text-[10px]">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span className="text-[10px]">Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
