import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Sparkles,
  History,
  Plus,
  BookOpen,
  BarChart2,
  Users,
  GraduationCap,
} from 'lucide-react'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { MessageComposer } from '@/components/chat/MessageComposer'
import { chatApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { AgentId, Attachment, Message } from '@/types'
import { cn } from '@/lib/utils'
import { ArrowRight } from 'lucide-react'

const examplePrompts = [
  {
    icon: BookOpen,
    label: 'Summarise documentation',
    text: 'Summarise the remote work policy and highlight key equipment allowances.',
    agentId: 'knowledge' as AgentId,
    color: '#6366f1',
  },
  {
    icon: BarChart2,
    label: 'Analyse operational trends',
    text: 'What were the recurring patterns in our Q3 incident reports?',
    agentId: 'insights' as AgentId,
    color: '#8b5cf6',
  },
  {
    icon: Users,
    label: 'Draft meeting agenda',
    text: 'Create a 45-minute sprint planning agenda for a cross-functional squad.',
    agentId: 'collaborate' as AgentId,
    color: '#22d3ee',
  },
  {
    icon: GraduationCap,
    label: 'Design learning path',
    text: 'Build a 30-day onboarding path for a senior backend engineer.',
    agentId: 'onboard' as AgentId,
    color: '#10b981',
  },
]

export function ChatPage() {
  const { user } = useAuth()
  const firstName = user?.name ? user.name.split(' ')[0] : 'there'
  const [conversations, setConversations] = useState<Array<{ id: string; title: string; agent_id: string; created_at: string }>>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const selectConversation = useCallback(async (convId: string) => {
    setActiveConvId(convId)
    setIsLoading(true)
    try {
      const res = await chatApi.listMessages(convId)
      const mapped: Message[] = res.items.map((m) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant' | 'system',
        content: m.content,
        timestamp: new Date(m.created_at),
        agentId: (m.agent_id as AgentId) || 'auto',
      }))
      setMessages(mapped)
    } catch (err) {
      console.error('Failed to load messages for conversation:', err)
      setMessages([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load conversation list on mount
  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.listConversations()
      setConversations(res.items)
      if (res.items.length > 0 && !activeConvId) {
        selectConversation(res.items[0].id)
      }
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }, [activeConvId, selectConversation])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  const startNewChat = () => {
    setActiveConvId(null)
    setMessages([])
  }

  const handleSend = useCallback(
    async (content: string, agentId: AgentId, attachments: Attachment[]) => {
      let convId = activeConvId

      // If no active conversation, create one in SQLite first
      if (!convId) {
        try {
          const title = content.slice(0, 36) + (content.length > 36 ? '...' : '')
          const newConv = await chatApi.createConversation(title, agentId)
          convId = newConv.id
          setActiveConvId(convId)
          setConversations((prev) => [
            { id: newConv.id, title, agent_id: agentId, created_at: new Date().toISOString() },
            ...prev,
          ])
        } catch (err) {
          console.error('Failed to create conversation in backend:', err)
        }
      }

      // Add user message to local state
      const userMsg: Message = {
        id: `msg_${Date.now()}_user`,
        role: 'user',
        content,
        timestamp: new Date(),
        attachments,
      }

      // Add streaming placeholder
      const assistantId = `msg_${Date.now()}_assistant`
      const streamingMsg: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        agentId,
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, streamingMsg])
      setIsLoading(true)

      // Persist user message to SQLite backend if conversation exists
      if (convId) {
        try {
          await chatApi.sendMessage(convId, content, agentId)
        } catch (err) {
          console.error('Failed to save user message:', err)
        }
      }

      // Generate intelligent response based on agent
      await new Promise((r) => setTimeout(r, 600))

      const demoResponses: Record<AgentId, string> = {
        auto: `I've analyzed your prompt and routed it through the HYPERREALM orchestration pipeline.\n\nYour message has been **persisted to the SQLite database**.\n\n**Query:** "${content}"\n\nAll conversations, messages, and state are synchronized with the backend.`,
        knowledge: `**Knowledge Specialist Agent**\n\nI searched your workspace documentation and guidelines in SQLite.\n\n**Response to:** "${content}"\n\nAll matching company policies and runbooks are available in the Knowledge Hub.`,
        insights: `**Insights & Data Agent**\n\nHere is the analysis based on current workspace metrics:\n\n- Active tasks and sprint milestones are on schedule.\n- Incident rate is within SLA limits.\n\nPrompt logged for audit trail.`,
        collaborate: `**Collaborate Agent**\n\nI have logged your request into team coordination. You can convert this directly into an approval or task item in the Tasks & Approvals view.`,
        onboard: `**Onboarding & Learning Agent**\n\nI've tailored the recommended modules based on your role. Check "My Learning" to track progress on this topic.`,
      }

      const response = demoResponses[agentId] || demoResponses.auto

      // Persist assistant message to backend
      if (convId) {
        try {
          await chatApi.sendMessage(convId, response, agentId)
        } catch (err) {
          console.error('Failed to save assistant message:', err)
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: response, isStreaming: false }
            : m
        )
      )
      setIsLoading(false)
    },
    [activeConvId]
  )

  const handleExamplePrompt = (prompt: { text: string; agentId: AgentId }) => {
    handleSend(prompt.text, prompt.agentId, [])
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Chat history panel ─────────────────────────────────────────── */}
      <div
        className={cn(
          'flex-shrink-0 border-r border-[var(--border-default)] bg-[var(--bg-surface)]',
          'flex flex-col transition-all duration-300',
          showHistory ? 'w-64' : 'w-0 overflow-hidden border-0'
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-default)]">
          <span className="text-sm font-semibold text-[var(--text-secondary)]">History</span>
          <button
            onClick={startNewChat}
            className="flex items-center gap-1.5 text-xs text-[var(--accent-indigo)] hover:underline"
          >
            <Plus className="h-3 w-3" />
            New
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="p-3 text-xs text-center text-[var(--text-muted)]">No conversations yet</div>
          ) : (
            conversations.map((h) => (
              <button
                key={h.id}
                onClick={() => selectConversation(h.id)}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-[var(--radius-md)] text-sm transition-colors',
                  activeConvId === h.id
                    ? 'bg-indigo-500/15 text-[var(--accent-indigo)] font-medium border border-indigo-500/30'
                    : 'hover:bg-[var(--bg-elevated)] text-[var(--text-primary)]'
                )}
              >
                <p className="truncate text-xs">{h.title || 'Conversation'}</p>
                <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
                  {new Date(h.created_at).toLocaleDateString()}
                </p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* ── Main chat area ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Top bar */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 h-16 border-b border-[var(--border-default)] bg-[var(--bg-surface)]/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistory((v) => !v)}
              className={cn(
                'p-2 rounded-xl transition-all duration-200',
                showHistory
                  ? 'bg-purple-500/15 text-purple-600 dark:text-purple-300'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
              )}
              aria-label="Toggle chat history"
              title="Chat history"
            >
              <History className="h-4.5 w-4.5" />
            </button>

            <div className="flex items-center gap-2.5">
              <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-[#4285f4] via-[#9b72cf] to-[#d96570] flex items-center justify-center shadow-[0_0_12px_rgba(155,114,207,0.3)]">
                <Sparkles className="h-3.5 w-3.5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="font-display text-sm font-semibold tracking-tight text-[var(--text-primary)] leading-tight">
                  Copilot Intelligence
                </span>
                <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1.5 leading-none">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  SQLite Synced & Active
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={startNewChat}
              className="flex items-center gap-1.5 h-8 px-3.5 rounded-full text-xs font-medium text-[var(--text-secondary)] border border-[var(--border-default)] hover:border-purple-500/30 hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] hover:shadow-sm transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              New Chat
            </button>
          </div>
        </div>

        {/* Messages / Empty state */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 gemini-aurora">
          {isEmpty ? (
            <div className="h-full flex flex-col items-center justify-center max-w-3xl mx-auto py-8">
              {/* Gemini-style Hero */}
              <div className="text-center mb-10 w-full animate-fade-in">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 border border-purple-500/25 text-xs font-medium text-purple-600 dark:text-purple-300 mb-6 shadow-sm">
                  <Sparkles className="h-3.5 w-3.5 text-purple-500 animate-pulse-subtle" />
                  <span>Next-Gen Enterprise Copilot • Gemini & Vertex AI</span>
                </div>
                
                <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-[var(--text-primary)] mb-3 leading-tight">
                  <span className="text-gemini">Hello, {firstName}</span>
                  <br />
                  <span className="text-[var(--text-secondary)] font-normal text-2xl sm:text-3xl md:text-4xl">
                    Where should we begin today?
                  </span>
                </h1>
                
                <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-md mx-auto">
                  Select an agent prompt below or ask any question. All conversations are synced in real time.
                </p>
              </div>

              {/* Example prompt cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full">
                {examplePrompts.map((p) => {
                  const Icon = p.icon
                  return (
                    <button
                      key={p.label}
                      onClick={() => handleExamplePrompt(p)}
                      className="group relative flex items-start gap-4 p-4.5 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] hover:border-purple-500/35 hover:shadow-[0_8px_24px_-4px_rgba(155,114,207,0.18)] hover:-translate-y-0.5 transition-all duration-200 text-left cursor-pointer"
                    >
                      <div
                        className="h-9 w-9 flex-shrink-0 rounded-xl flex items-center justify-center mt-0.5 shadow-sm transition-transform group-hover:scale-105"
                        style={{ backgroundColor: `${p.color}18` }}
                      >
                        <Icon className="h-4.5 w-4.5" style={{ color: p.color }} />
                      </div>
                      <div className="flex-1 min-w-0 pr-4">
                        <p className="text-xs font-semibold text-[var(--text-primary)] mb-1 group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors">
                          {p.label}
                        </p>
                        <p className="text-xs text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                          {p.text}
                        </p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-[var(--text-muted)] opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-200 self-center" />
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="flex-shrink-0 p-4 sm:p-5 max-w-4xl w-full mx-auto">
          <MessageComposer onSend={handleSend} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
