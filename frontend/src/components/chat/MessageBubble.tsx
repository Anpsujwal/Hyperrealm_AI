import { useState } from 'react'
import { cn, formatRelativeTime, getInitials } from '@/lib/utils'
import { AGENTS } from '@/types'
import type { Message } from '@/types'
import { TypingIndicator } from '@/components/ui/Feedback'
import { Sparkles, Copy, Check, ThumbsUp, ThumbsDown, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { MarkdownContent } from './MarkdownContent'
import { MeetingProposalCard } from './MeetingProposalCard'

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
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const [citationsExpanded, setCitationsExpanded] = useState(true)
  const isUser = message.role === 'user'
  const agent = message.agentId ? AGENTS.find((a) => a.id === message.agentId) : null
  const agentColor = message.agentId ? AGENT_COLORS[message.agentId] : '#9b72cf'

  const handleCopy = () => {
    if (!message.content) return
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className={cn(
        'flex gap-3.5 animate-slide-up group/msg w-full',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      {isUser ? (
        <div className="flex-shrink-0 h-9 w-9 rounded-full bg-gradient-to-tr from-[#4285f4] via-[#9b72cf] to-[#d96570] flex items-center justify-center text-xs font-bold text-white shadow-md ring-2 ring-[var(--bg-surface)]">
          {getInitials(user?.name ?? 'You')}
        </div>
      ) : (
        <div
          className="flex-shrink-0 h-9 w-9 rounded-xl flex items-center justify-center shadow-md border transition-all duration-200"
          style={{
            backgroundColor: `${agentColor}22`,
            borderColor: `${agentColor}40`,
          }}
        >
          <Sparkles className="h-4.5 w-4.5" style={{ color: agentColor }} />
        </div>
      )}

      <div className={cn('flex flex-col gap-1.5 max-w-[85%] sm:max-w-[78%]', isUser && 'items-end')}>
        {/* Agent label */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-0.5">
            <span
              className="text-xs font-bold tracking-tight"
              style={{ color: agentColor }}
            >
              {agent?.name || 'Copilot AI'}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 dark:bg-none dark:bg-zinc-800 border border-purple-500/20 dark:border-zinc-700 text-purple-600 dark:text-zinc-300 font-semibold">
              Gemini 3.8 Flash
            </span>
            {message.delegatedAgents && message.delegatedAgents.length > 1 && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/30 text-purple-300 font-semibold flex items-center gap-1">
                ⚡ Multi-Agent ({message.delegatedAgents.join(' → ')})
              </span>
            )}
          </div>
        )}

        {/* Bubble */}
        <div
          className={cn(
            'px-5 py-4 text-sm leading-relaxed transition-all duration-200',
            isUser
              ? 'rounded-2xl rounded-tr-xs bg-gradient-to-tr from-indigo-600 via-indigo-600 to-violet-600 dark:bg-none dark:bg-indigo-600 text-white shadow-md dark:shadow-none'
              : 'rounded-2xl rounded-tl-xs bg-[var(--bg-surface)] border border-[var(--border-default)] dark:border-zinc-800 text-[var(--text-primary)] shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] dark:shadow-none hover:border-indigo-500/30'
          )}
        >
          {message.isStreaming ? (
            <div className="flex items-center gap-2 py-1">
              <TypingIndicator />
              <span className="text-xs text-[var(--text-muted)] animate-pulse">Thinking & retrieving policies…</span>
            </div>
          ) : isUser ? (
            <div className="whitespace-pre-wrap font-normal selection:bg-white/20">{message.content}</div>
          ) : (
            <MarkdownContent content={message.content} />
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

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2.5 space-y-2 w-full">
            <button
              onClick={() => setCitationsExpanded((v) => !v)}
              className="flex items-center justify-between w-full text-[11px] font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors py-1 cursor-pointer"
            >
              <div className="flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
                <span>Grounded Citations ({message.citations.length})</span>
              </div>
              {citationsExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>

            {citationsExpanded && (
              <div className="grid gap-2 animate-fade-in">
                {message.citations.map((cite, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-[var(--bg-elevated)]/80 border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] hover:border-indigo-500/40 hover:bg-[var(--bg-elevated)] transition-all shadow-xs"
                  >
                    <div className="flex items-center justify-between mb-1.5 gap-2">
                      <span className="font-semibold text-[var(--text-primary)] truncate">{cite.title}</span>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                        cite.scope === 'official' || cite.source_type === 'official_guideline'
                          ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30'
                          : 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      }`}>
                        {cite.scope || (cite.source_type === 'official_guideline' ? 'official' : 'enterprise')} {cite.version || cite.guideline_version ? `v${cite.version || cite.guideline_version}` : ''}
                      </span>
                    </div>
                    {cite.passage && (
                      <p className="text-[11px] text-[var(--text-muted)] italic leading-relaxed line-clamp-3">
                        "{cite.passage}"
                      </p>
                    )}
                    {cite.section && (
                      <div className="mt-1 text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                        <span>Section: {cite.section}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Proposed Actions */}
        {message.proposedActions && message.proposedActions.length > 0 && (
          <div className="mt-2.5 space-y-2 w-full">
            <span className="text-[11px] font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" />
              Proposed Actions ({message.proposedActions.length})
            </span>
            <div className="grid gap-2">
              {message.proposedActions.map((act, idx) =>
                act.action_type === 'schedule_meeting_proposal' ? (
                  <MeetingProposalCard
                    key={idx}
                    proposalId={act.proposal_id}
                    payload={act.payload}
                    title={act.title}
                    description={act.description}
                  />
                ) : (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-purple-500/8 border border-purple-500/25 text-xs shadow-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-[var(--text-primary)]">{act.title}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-400 uppercase font-bold">
                        {act.action_type}
                      </span>
                    </div>
                    {act.description && (
                      <p className="text-[11px] text-[var(--text-secondary)] mb-2 leading-relaxed">{act.description}</p>
                    )}
                    {act.requires_approval ? (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-medium text-amber-400 bg-amber-500/15 px-2.5 py-0.5 rounded-full border border-amber-500/25">
                          Requires Lead / Admin Sign-off
                        </span>
                      </div>
                    ) : null}
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Action toolbar & Timestamp */}
        <div className="flex items-center gap-3 px-1 mt-0.5">
          <p className="text-[10px] text-[var(--text-muted)]">
            {formatRelativeTime(message.timestamp)}
          </p>

          {!isUser && !message.isStreaming && (
            <div className="opacity-0 group-hover/msg:opacity-100 flex items-center gap-1.5 transition-all">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
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

              <button
                onClick={() => setFeedback((f) => (f === 'up' ? null : 'up'))}
                className={cn(
                  'p-1 rounded text-[var(--text-muted)] hover:text-emerald-400 hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer',
                  feedback === 'up' && 'text-emerald-400 bg-emerald-500/15'
                )}
                title="Helpful"
                aria-label="Mark helpful"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>

              <button
                onClick={() => setFeedback((f) => (f === 'down' ? null : 'down'))}
                className={cn(
                  'p-1 rounded text-[var(--text-muted)] hover:text-rose-400 hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer',
                  feedback === 'down' && 'text-rose-400 bg-rose-500/15'
                )}
                title="Not helpful"
                aria-label="Mark not helpful"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
