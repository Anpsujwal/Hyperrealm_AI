import { useState, useRef, useCallback, type KeyboardEvent } from 'react'
import {
  Send,
  Paperclip,
  Mic,
  MicOff,
  Sparkles,
  BookOpen,
  BarChart2,
  Users,
  GraduationCap,
  ChevronDown,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { AGENTS } from '@/types'
import type { AgentId, Attachment } from '@/types'
import * as PopoverPrimitive from '@radix-ui/react-popover'

const AGENT_ICONS: Record<AgentId, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  auto: Sparkles,
  knowledge: BookOpen,
  insights: BarChart2,
  collaborate: Users,
  onboard: GraduationCap,
}

interface MessageComposerProps {
  onSend: (content: string, agentId: AgentId, attachments: Attachment[]) => void
  isLoading?: boolean
  disabled?: boolean
  placeholder?: string
}

export function MessageComposer({
  onSend,
  isLoading,
  disabled,
  placeholder = 'Ask HYPERREALM anything…',
}: MessageComposerProps) {
  const [text, setText] = useState('')
  const [selectedAgent, setSelectedAgent] = useState<AgentId>('auto')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [agentPickerOpen, setAgentPickerOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const currentAgent = AGENTS.find((a) => a.id === selectedAgent)!
  const AgentIcon = AGENT_ICONS[selectedAgent]

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed, selectedAgent, attachments)
    setText('')
    setAttachments([])
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [text, selectedAgent, attachments, isLoading, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    const newAttachments: Attachment[] = files.map((f) => ({
      id: `att_${Date.now()}_${f.name}`,
      name: f.name,
      type: f.type,
      size: f.size,
    }))
    setAttachments((prev) => [...prev, ...newAttachments])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id))
  }

  // NOTE: Phase 01 — microphone toggle is a labelled placeholder. Real STT connects in a later phase.
  const toggleRecording = () => {
    setIsRecording((v) => !v)
  }

  const canSend = text.trim().length > 0 && !isLoading && !disabled

  return (
    <div className="flex flex-col gap-2">
      {/* Attachment chips */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 px-1">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] text-xs text-[var(--text-secondary)]"
            >
              <Paperclip className="h-3 w-3 flex-shrink-0" />
              <span className="max-w-[140px] truncate">{att.name}</span>
              <button
                onClick={() => removeAttachment(att.id)}
                className="text-[var(--text-muted)] hover:text-[var(--accent-rose)] transition-colors"
                aria-label={`Remove ${att.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Composer box */}
      <div
        className={cn(
          'flex flex-col rounded-[26px] border transition-all duration-300 relative',
          'bg-[var(--bg-surface)]/90 backdrop-blur-xl border-[var(--border-strong)]',
          'focus-within:border-purple-500/60 focus-within:shadow-[0_0_30px_rgba(155,114,207,0.22)] focus-within:ring-2 focus-within:ring-purple-500/20',
          'shadow-[0_12px_32px_-4px_rgba(0,0,0,0.15)] dark:shadow-[0_12px_32px_-4px_rgba(0,0,0,0.5)]'
        )}
      >
        {/* Text area */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          aria-label="Message input"
          className={cn(
            'w-full bg-transparent px-5 pt-4 pb-2 resize-none',
            'text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]',
            'focus:outline-none',
            'min-h-[46px] max-h-[200px]',
            'disabled:opacity-50'
          )}
        />

        {/* Bottom toolbar */}
        <div className="flex items-center gap-2 px-4 pb-3.5 pt-1">
          {/* File attach */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            aria-hidden="true"
            id="composer-file-input"
            onChange={handleFileSelect}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="flex items-center justify-center h-8 w-8 rounded-full text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors disabled:opacity-40"
            aria-label="Attach file"
            title="Attach file"
          >
            <Paperclip className="h-4 w-4" />
          </button>

          {/* Microphone — labelled placeholder */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={disabled}
            className={cn(
              'flex items-center justify-center h-8 w-8 rounded-full transition-all',
              isRecording
                ? 'text-[var(--accent-rose)] bg-rose-500/15 animate-pulse-subtle'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]',
              'disabled:opacity-40'
            )}
            aria-label={isRecording ? 'Stop recording (placeholder)' : 'Start voice input (placeholder)'}
            title={isRecording ? 'Recording… (STT coming in Phase 02)' : 'Voice input (coming in Phase 02)'}
          >
            {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>

          {/* Agent selector */}
          <PopoverPrimitive.Root open={agentPickerOpen} onOpenChange={setAgentPickerOpen}>
            <PopoverPrimitive.Trigger asChild>
              <button
                type="button"
                className={cn(
                  'flex items-center gap-1.5 h-7.5 px-3 rounded-full',
                  'text-xs font-medium transition-all',
                  'border border-[var(--border-default)] bg-[var(--bg-elevated)]/60',
                  'hover:border-purple-500/40 hover:bg-[var(--bg-elevated)]',
                  'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                )}
                aria-label="Select agent"
                aria-haspopup="listbox"
                aria-expanded={agentPickerOpen}
              >
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: currentAgent.color }}
                />
                <AgentIcon className="h-3.5 w-3.5" style={{ color: currentAgent.color }} />
                <span>{currentAgent.name}</span>
                <ChevronDown className="h-3 w-3 text-[var(--text-muted)]" />
              </button>
            </PopoverPrimitive.Trigger>
            <PopoverPrimitive.Portal>
              <PopoverPrimitive.Content
                side="top"
                align="start"
                sideOffset={8}
                className={cn(
                  'z-50 w-72 rounded-2xl p-2.5',
                  'bg-[var(--bg-surface)] border border-[var(--border-strong)]',
                  'shadow-2xl backdrop-blur-xl',
                  'animate-slide-up'
                )}
              >
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-2 mb-2">
                  Specialist Intelligence Agent
                </p>
                <div role="listbox" aria-label="Agent selection" className="space-y-1">
                  {AGENTS.map((agent) => {
                    const Icon = AGENT_ICONS[agent.id]
                    return (
                      <button
                        key={agent.id}
                        role="option"
                        aria-selected={selectedAgent === agent.id}
                        onClick={() => {
                          setSelectedAgent(agent.id)
                          setAgentPickerOpen(false)
                        }}
                        className={cn(
                          'w-full flex items-start gap-3 px-3 py-2.5 rounded-xl',
                          'text-left transition-all duration-150',
                          'hover:bg-[var(--bg-elevated)]',
                          selectedAgent === agent.id && 'bg-purple-500/10 border border-purple-500/25'
                        )}
                      >
                        <div
                          className="mt-0.5 h-6.5 w-6.5 flex-shrink-0 rounded-lg flex items-center justify-center shadow-xs"
                          style={{ backgroundColor: `${agent.color}20` }}
                        >
                          <Icon className="h-3.5 w-3.5" style={{ color: agent.color }} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-[var(--text-primary)]">
                            {agent.name}
                          </p>
                          <p className="text-[11px] text-[var(--text-muted)] leading-snug">
                            {agent.description}
                          </p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </PopoverPrimitive.Content>
            </PopoverPrimitive.Portal>
          </PopoverPrimitive.Root>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Hint */}
          <span className="hidden sm:block text-[11px] text-[var(--text-muted)] mr-1">
            Shift + Return for newline
          </span>

          {/* Send Button with Gemini Gradient */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend}
            className={cn(
              'flex items-center justify-center h-8.5 w-8.5 rounded-full transition-all duration-200',
              canSend
                ? 'bg-gradient-to-tr from-[#4285f4] via-[#9b72cf] to-[#d96570] text-white shadow-[0_0_20px_rgba(155,114,207,0.45)] hover:scale-105 active:scale-95 cursor-pointer'
                : 'bg-[var(--bg-elevated)] text-[var(--text-muted)] cursor-not-allowed opacity-50'
            )}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
