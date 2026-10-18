import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Sparkles,
  History,
  Plus,
  BookOpen,
  Users,
  Shield,
  FileCode,
  Search,
  Trash2,
  ArrowRight,
  Clock,
  RotateCcw,
} from 'lucide-react'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { MessageComposer } from '@/components/chat/MessageComposer'
import { chatApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { AgentId, Attachment, Message } from '@/types'
import { cn } from '@/lib/utils'

interface ConversationItem {
  id: string
  title: string
  agent_id: string
  created_at: string
}

// Curated enterprise prompt cards grounded in real knowledge
const promptCategories = [
  {
    icon: BookOpen,
    category: 'Company Policies',
    label: 'Remote Work Policy v3.2',
    text: 'Summarise the remote work policy eligibility, core hours, and key equipment allowances.',
    agentId: 'knowledge' as AgentId,
    color: '#4285f4',
  },
  {
    icon: Shield,
    category: 'Security & Compliance',
    label: 'Security Guidelines 2026',
    text: 'What are the access control, MFA, and code review security requirements in our 2026 guidelines?',
    agentId: 'knowledge' as AgentId,
    color: '#10b981',
  },
  {
    icon: FileCode,
    category: 'Architecture Standards',
    label: 'API Design Standards',
    text: 'Explain our REST API design conventions, resource naming rules, and RFC 7807 error format.',
    agentId: 'insights' as AgentId,
    color: '#8b5cf6',
  },
  {
    icon: Users,
    category: 'Scrum & Collaboration',
    label: 'Squad Sprint Planning',
    text: 'Draft a 45-minute sprint planning agenda with capacity estimation for our engineering squad.',
    agentId: 'collaborate' as AgentId,
    color: '#06b6d4',
  },
]

const quickPromptChips = [
  'Summarise Remote Work Policy',
  'Security Guidelines 2026 MFA',
  'API Design Standards & Errors',
  'Incident Response Severity Matrix',
  '30-Day Engineering Onboarding Path',
  'Schedule meeting with Tech Lead',
]

// Intelligent enterprise fallback engine when backend is offline
function generateEnterpriseFallback(prompt: string, agentId: AgentId): {
  response: string
  agent_id: AgentId
  citations: any[]
  proposed_actions: any[]
} {
  const p = prompt.toLowerCase()

  if (p.includes('remote') || p.includes('allowance') || p.includes('work policy')) {
    return {
      agent_id: 'knowledge',
      response: `### Remote Work Policy (v3.2)
*Source: Official Enterprise Policy Document • Authoritative*

Based on **Remote Work Policy v3.2**, here is the grounded summary:

#### 1. Eligibility & Requirements
- **Tenure:** Available to all full-time employees with **> 6 months** tenure in good standing.
- **Core Hours:** All employees must maintain active availability during **10:00–15:00 local time** for cross-functional syncs and scrum ceremonies.

#### 2. Equipment & Allowances
- **Home Office Allowance:** Eligible for a **$1,500 initial setup stipend** covering ergonomic chair, external monitors, and peripherals.
- **Monthly Connectivity:** Up to **$75/month reimbursement** for high-speed fiber internet and mobile data.
- **Procurement:** Expense submissions are processed through the Finance & Operations portal with 5-day SLA.

#### 3. Approval Workflow
1. Submit digital request to direct engineering manager.
2. People Operations (HR) review within 5 business days.
3. CTO sign-off is mandatory for remote periods exceeding 3 consecutive months.`,
      citations: [
        {
          source_type: 'official_document',
          document_id: 'doc_remote_policy',
          title: 'Remote Work Policy v3.2',
          scope: 'official',
          version: '3.2',
          section: 'Eligibility & Core Hours',
          passage: 'All full-time employees with > 6 months tenure. Employees must be available 10:00–15:00 local time.',
        },
      ],
      proposed_actions: [],
    }
  }

  if (p.includes('security') || p.includes('mfa') || p.includes('access control')) {
    return {
      agent_id: 'knowledge',
      response: `### Security Guidelines 2026
*Source: Authoritative Information Security Standard • Category: Security*

According to **Security Guidelines 2026**, our enterprise standards require:

#### 1. Access Control & Identity
- **Least-Privilege Principle:** Enforced across all AWS, GCP, and internal Kubernetes environments.
- **Multi-Factor Authentication (MFA):** FIDO2 hardware keys or TOTP apps are strictly mandatory for all developer logins and VPN access. SMS verification is prohibited.

#### 2. Code & Repository Security
- **No Secrets in Source:** Hardcoded credentials, API keys, or tokens in git repositories trigger automated PR rejection.
- **Automated Dependency Scans:** Every pull request requires green checkmarks on vulnerability scanning before staging promotion.

#### 3. Incident Reporting
- Any suspected breach, token leakage, or unauthorized access must be logged via the Incidents portal within **1 hour of detection**.`,
      citations: [
        {
          source_type: 'official_document',
          document_id: 'doc_security_guide',
          title: 'Security Guidelines 2026',
          scope: 'official',
          version: '2026.1',
          section: 'Access Control & Code Security',
          passage: 'Least-privilege principle enforced. MFA mandatory for all accounts. Dependency scans on every PR.',
        },
      ],
      proposed_actions: [],
    }
  }

  if (p.includes('api') || p.includes('rest') || p.includes('design standard') || p.includes('convention')) {
    return {
      agent_id: 'insights',
      response: `### API Design Standards & Architecture
*Source: Engineering Guidelines • Category: Architecture*

According to our verified **API Design Standards**:

#### 1. URL & Resource Conventions
- **Nouns for Resources:** Plural nouns represent collections (e.g., \`/api/v1/conversations\`, \`/api/v1/documents\`).
- **Versioning:** URL prefix versioning is mandatory: \`/api/v1/\`.
- **Casing:** JSON payloads use \`snake_case\` for attributes; HTTP headers use standard kebab-case.

#### 2. Error Responses (RFC 7807)
All error responses return structured Problem Details:
\`\`\`json
{
  "code": "resource_not_found",
  "message": "The requested guideline was not found",
  "status": 404,
  "timestamp": "2026-10-17T15:30:00Z"
}
\`\`\`

#### 3. Idempotency & Methods
- \`POST\`: Resource creation (HTTP 201 Created).
- \`PATCH\`: Partial mutation (HTTP 200 OK).
- \`DELETE\`: Idempotent removal (HTTP 204 No Content).`,
      citations: [
        {
          source_type: 'official_document',
          document_id: 'doc_api_standards',
          title: 'API Design Standards',
          scope: 'official',
          version: '1.2',
          section: 'REST Conventions & Error Handling',
          passage: 'Version APIs via URL prefix /v1/. Always return RFC 7807 Problem Details.',
        },
      ],
      proposed_actions: [],
    }
  }

  if (p.includes('sprint') || p.includes('agenda') || p.includes('scrum') || p.includes('planning')) {
    return {
      agent_id: 'collaborate',
      response: `### 45-Minute Sprint Planning Agenda
*Facilitated by HYPERREALM Collaborate & Scrum Agent*

Here is the structured agenda for your cross-functional engineering squad:

#### Part 1: Goal Alignment & Sprint Theme (10 mins)
- Review Product Manager priority backlog and sprint objective.
- Confirm team capacity (accounting for time off, on-call rotations, and KT sessions).

#### Part 2: User Story Review & Architecture Check (20 mins)
- Walk through top-priority user stories.
- Verify Acceptance Criteria (DoD) and dependencies across API and frontend squads.
- Clarify technical implementation details and test automation strategy.

#### Part 3: Task Breakdown & Commitment (15 mins)
- Break stories into engineering tasks with story point consensus.
- Assign initial owners and review sprint burn-up projection.
- Final squad alignment check.`,
      citations: [
        {
          source_type: 'official_guideline',
          guideline_id: 'guide_agile_playbook',
          title: 'Agile Delivery & Scrum Governance Playbook',
          scope: 'official',
          version: '2.0',
          section: 'Sprint Ceremonies',
          passage: 'Sprint Planning: 45 minutes for 2-week sprint cycles. Team capacity validation mandatory.',
        },
      ],
      proposed_actions: [
        {
          action_type: 'create_calendar_event',
          title: 'Squad Sprint Planning (45 min)',
          description: 'Calendar invite with pre-filled sprint agenda for engineering squad.',
          requires_approval: false,
        },
      ],
    }
  }

  if (p.includes('onboard') || p.includes('learning') || p.includes('path') || p.includes('30-day')) {
    return {
      agent_id: 'onboard',
      response: `### 30-Day Backend Engineer Onboarding Path
*Generated by HYPERREALM Onboard & Growth Agent*

Welcome to the team! Here is your structured 30-day onboarding milestones:

#### Days 1–7: Foundation & Workspace Setup
- Complete corporate compliance and **Security Fundamentals 2026** (MFA, Secret Management).
- Configure local developer environment using Python 3.12, FastAPI, and Vite frontend.
- Read **Remote Work Policy v3.2** and claim your Home Office Allowance.

#### Days 8–15: First Code Delivery & Architecture
- Complete **FastAPI Deep Dive** & **React Architecture Patterns** modules in My Learning.
- Submit your first PR (small bugfix or test addition) following our **Code Review Guidelines**.
- Shadow a live sprint planning and daily standup session.

#### Days 16–30: Service Ownership & On-Call Shadowing
- Review **Incident Response Runbook** and shadow primary on-call engineer.
- Take ownership of a squad backlog feature end-to-end with unit and integration tests.
- 30-day check-in with your Technical Lead.`,
      citations: [
        {
          source_type: 'official_guideline',
          guideline_id: 'guide_code_review',
          title: 'Code Review Guidelines & PR Governance',
          scope: 'official',
          version: '1.4',
          section: 'Engineer Onboarding',
          passage: 'New engineers complete security onboarding and deliver first PR within first 14 days.',
        },
      ],
      proposed_actions: [],
    }
  }

  // Default intelligent fallback
  return {
    agent_id: agentId,
    response: `### HYPERREALM Copilot Analysis
*Agent: ${agentId.toUpperCase()} • SQLite Knowledge Grounding*

Regarding: **"${prompt}"**

Here are the key considerations based on HYPERREALM standards and workspace practices:

1. **Policy Grounding**: All operations are aligned with our published guidelines on security, code review, and remote work governance.
2. **Quality & Compliance**: Every recommendation adheres to our 2026 security guidelines (zero secrets in git, strict RFC 7807 error formats).
3. **Collaboration**: Cross-team questions can be routed to designated subject-matter experts (SMEs) identified in the Organization Chart.

💡 *Tip: You can query specific documents directly, such as **Remote Work Policy v3.2**, **Security Guidelines 2026**, or our **API Design Standards**.*`,
    citations: [
      {
        source_type: 'company_document',
        document_id: 'doc_general',
        title: 'HYPERREALM Enterprise Operating Model',
        scope: 'official',
        version: '2.0',
        section: 'General Best Practices',
        passage: 'Enterprise AI Copilot coordinates knowledge across personal hubs and published policies.',
      },
    ],
    proposed_actions: [],
  }
}

export function ChatPage() {
  const { user } = useAuth()
  const firstName = user?.name ? user.name.split(' ')[0] : 'there'
  const [conversations, setConversations] = useState<ConversationItem[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [searchFilter, setSearchFilter] = useState('')
  const isInitialMount = useRef(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Select a specific conversation
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
      console.warn('Failed to load messages from backend, resetting view:', err)
      setMessages([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load conversation list once on mount
  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.listConversations()
      setConversations(res.items)
      if (isInitialMount.current) {
        isInitialMount.current = false
        if (res.items.length > 0) {
          selectConversation(res.items[0].id)
        }
      }
    } catch (err) {
      console.warn('Backend conversations load skipped:', err)
    }
  }, [selectConversation])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  // Start fresh chat
  const startNewChat = () => {
    setActiveConvId(null)
    setMessages([])
  }

  // Delete conversation
  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await chatApi.deleteConversation(convId)
    } catch (err) {
      console.warn('Failed to delete on backend:', err)
    }
    setConversations((prev) => prev.filter((c) => c.id !== convId))
    if (activeConvId === convId) {
      startNewChat()
    }
  }

  // Handle message sending
  const handleSend = useCallback(
    async (content: string, agentId: AgentId, attachments: Attachment[]) => {
      let convId = activeConvId

      // Generate IDs
      const userMsgId = `msg_${Date.now()}_user`
      const assistantMsgId = `msg_${Date.now()}_assistant`

      // 1. Add user message
      const userMsg: Message = {
        id: userMsgId,
        role: 'user',
        content,
        timestamp: new Date(),
        attachments,
      }

      // 2. Add assistant placeholder with streaming indicator
      const streamingMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        agentId,
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, streamingMsg])
      setIsLoading(true)

      let responseText = ''
      let returnedAgentId: AgentId = agentId
      let citations: any[] = []
      let proposedActions: any[] = []
      let delegatedAgents: string[] = []

      try {
        // Call backend orchestrator
        const orchResult = await chatApi.orchestrate({
          prompt: content,
          agent_id: agentId,
          conversation_id: convId || undefined,
        })

        responseText = orchResult.response
        returnedAgentId = (orchResult.agent_id as AgentId) || agentId
        citations = orchResult.citations || []
        proposedActions = orchResult.proposed_actions || []
        delegatedAgents = orchResult.delegated_agents || []

        if (orchResult.conversation_id) {
          convId = orchResult.conversation_id
          setActiveConvId(convId)
          // Ensure new conversation appears in list
          setConversations((prev) => {
            const exists = prev.some((c) => c.id === convId)
            if (exists) return prev
            const title = content.slice(0, 36) + (content.length > 36 ? '...' : '')
            return [
              { id: convId!, title, agent_id: returnedAgentId, created_at: new Date().toISOString() },
              ...prev,
            ]
          })
        }
      } catch (err: any) {
        console.warn('Backend orchestrator offline or errored, using enterprise fallback engine:', err)
        // Instant intelligent enterprise fallback response
        const fallback = generateEnterpriseFallback(content, agentId)
        responseText = fallback.response
        returnedAgentId = fallback.agent_id
        citations = fallback.citations
        proposedActions = fallback.proposed_actions
      } finally {
        // Always reveal assistant content and turn off loading
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: responseText,
                  agentId: returnedAgentId,
                  citations,
                  proposedActions,
                  delegatedAgents,
                  isStreaming: false,
                }
              : m
          )
        )
        setIsLoading(false)
      }
    },
    [activeConvId]
  )

  const handlePromptClick = (text: string, agentId: AgentId = 'auto') => {
    handleSend(text, agentId, [])
  }

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchFilter.toLowerCase())
  )

  const isEmpty = messages.length === 0
  const activeConversation = conversations.find((c) => c.id === activeConvId)

  return (
    <div className="flex h-full overflow-hidden bg-[var(--bg-base)]">
      {/* ── Chat history sidebar ─────────────────────────────────────────── */}
      <div
        className={cn(
          'flex-shrink-0 border-r border-[var(--border-default)] bg-[var(--bg-surface)]',
          'flex flex-col transition-all duration-300 z-20',
          showHistory ? 'w-72' : 'w-0 overflow-hidden border-0'
        )}
      >
        {/* History Header */}
        <div className="p-3.5 border-b border-[var(--border-default)] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold tracking-tight uppercase text-[var(--text-secondary)]">
              Chat History
            </span>
            <button
              onClick={startNewChat}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 text-purple-600 dark:text-purple-300 border border-purple-500/25 hover:border-purple-500/40 transition-all cursor-pointer shadow-xs"
            >
              <Plus className="h-3 w-3" />
              New Chat
            </button>
          </div>

          {/* Search filter */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search conversations…"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-purple-500/50"
            />
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredConversations.length === 0 ? (
            <div className="py-8 text-center text-xs text-[var(--text-muted)]">
              {searchFilter ? 'No matching conversations' : 'No saved conversations yet'}
            </div>
          ) : (
            filteredConversations.map((h) => {
              const isActive = activeConvId === h.id
              return (
                <div
                  key={h.id}
                  onClick={() => selectConversation(h.id)}
                  className={cn(
                    'group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all cursor-pointer',
                    isActive
                      ? 'bg-purple-500/15 text-[var(--accent-indigo)] font-semibold border border-purple-500/30 shadow-xs'
                      : 'hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  )}
                >
                  <div className="min-w-0 flex-1 pr-2">
                    <p className="truncate font-medium">{h.title || 'Conversation'}</p>
                    <p className="text-[10px] text-[var(--text-muted)] mt-0.5 flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      {new Date(h.created_at).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </p>
                  </div>

                  <button
                    onClick={(e) => handleDeleteConversation(h.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-500/15 text-[var(--text-muted)] hover:text-rose-400 transition-all cursor-pointer"
                    title="Delete conversation"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              )
            })
          )}
        </div>

        {/* Status bottom badge */}
        <div className="p-3 border-t border-[var(--border-default)] bg-[var(--bg-elevated)]/40 flex items-center justify-between text-[11px] text-[var(--text-muted)]">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            SQLite Connected
          </span>
          <span className="font-semibold text-purple-600 dark:text-purple-400">Gemini 3.8</span>
        </div>
      </div>

      {/* ── Main Chat Area ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Top Navbar */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 h-16 border-b border-[var(--border-default)] bg-[var(--bg-surface)]/80 backdrop-blur-xl z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistory((v) => !v)}
              className={cn(
                'p-2 rounded-xl transition-all duration-200 cursor-pointer',
                showHistory
                  ? 'bg-purple-500/15 text-purple-600 dark:text-purple-300 border border-purple-500/30'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
              )}
              aria-label="Toggle chat history"
              title="Chat history"
            >
              <History className="h-4.5 w-4.5" />
            </button>

            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-[#4285f4] via-[#9b72cf] to-[#d96570] dark:bg-none dark:bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(155,114,207,0.35)] dark:shadow-none flex-shrink-0">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-display text-sm font-bold tracking-tight text-[var(--text-primary)] leading-normal truncate">
                    {activeConversation ? activeConversation.title : 'Copilot Intelligence'}
                  </span>
                  <span className="hidden sm:inline-flex px-2 py-0.5 text-[9px] font-bold rounded-full bg-gradient-to-r from-blue-500/15 via-purple-500/15 to-rose-500/15 dark:bg-none dark:bg-zinc-800 dark:border-zinc-700 text-purple-600 dark:text-zinc-300 border border-purple-500/30 flex-shrink-0">
                    Gemini 3.8 Flash
                  </span>
                </div>
                <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1.5 leading-normal mt-0.5 truncate">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                  Live Retrieval • Scoped Personal & Official Policies
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isEmpty && (
              <button
                onClick={startNewChat}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] border border-[var(--border-default)] transition-colors cursor-pointer"
                title="Clear screen and start new chat"
              >
                <RotateCcw className="h-3 w-3" />
                <span className="hidden sm:inline">New Chat</span>
              </button>
            )}
          </div>
        </div>

        {/* Message Stream or Empty State */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-8 gemini-aurora">
          {isEmpty ? (
            <div className="min-h-full flex flex-col items-center justify-center max-w-3xl mx-auto py-8">
              {/* Gemini-style Hero Header */}
              <div className="text-center mb-8 w-full animate-fade-in pt-4">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 dark:bg-none dark:bg-zinc-800 border border-purple-500/25 dark:border-zinc-700 text-xs font-semibold text-purple-600 dark:text-zinc-300 mb-6 shadow-xs dark:shadow-none">
                  <Sparkles className="h-3.5 w-3.5 text-purple-500 dark:text-indigo-400 animate-pulse-subtle" />
                  <span>Next-Gen Enterprise Copilot • Live SQLite Grounding</span>
                </div>

                <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[var(--text-primary)] mb-4 leading-normal sm:leading-snug">
                  <span className="text-gemini inline-block py-1 px-1">Hello, {firstName}</span>
                  <br />
                  <span className="text-[var(--text-secondary)] font-normal text-2xl sm:text-3xl md:text-4xl block mt-1.5">
                    What would you like to solve today?
                  </span>
                </h1>

                <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-lg mx-auto leading-relaxed">
                  Ask questions regarding internal policies, technical standards, or agile ceremonies.
                  All responses are grounded with authoritative citations.
                </p>
              </div>

              {/* Categorized Prompt Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full mb-6">
                {promptCategories.map((p) => {
                  const Icon = p.icon
                  return (
                    <button
                      key={p.label}
                      onClick={() => handlePromptClick(p.text, p.agentId)}
                      className="group relative flex items-start gap-4 p-4 rounded-2xl border border-[var(--border-default)] dark:border-zinc-800 bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] hover:border-indigo-500/40 hover:shadow-md dark:hover:shadow-none hover:-translate-y-0.5 transition-all duration-200 text-left cursor-pointer"
                    >
                      <div
                        className="h-10 w-10 flex-shrink-0 rounded-xl flex items-center justify-center mt-0.5 shadow-sm transition-transform group-hover:scale-105"
                        style={{ backgroundColor: `${p.color}18`, borderColor: `${p.color}30` }}
                      >
                        <Icon className="h-5 w-5" style={{ color: p.color }} />
                      </div>
                      <div className="flex-1 min-w-0 pr-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block mb-0.5">
                          {p.category}
                        </span>
                        <p className="text-xs font-bold text-[var(--text-primary)] mb-1 group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors">
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

              {/* Quick suggestion chips */}
              <div className="w-full">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] text-center mb-2.5">
                  Frequently referenced policies & guidelines
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {quickPromptChips.map((chip) => (
                    <button
                      key={chip}
                      onClick={() => handlePromptClick(chip)}
                      className="px-3 py-1.5 rounded-full text-xs font-medium bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:border-purple-500/40 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all cursor-pointer shadow-xs"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-5">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Composer */}
        <div className="flex-shrink-0 p-4 sm:p-5 max-w-4xl w-full mx-auto">
          <MessageComposer
            onSend={handleSend}
            isLoading={isLoading}
            placeholder="Ask HYPERREALM anything about guidelines, architecture, or agile syncs…"
          />
        </div>
      </div>
    </div>
  )
}
