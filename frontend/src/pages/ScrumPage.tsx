import { useState, useEffect, useMemo } from 'react'
import {
  CheckSquare,
  Plus,
  RefreshCw,
  X,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Users,
  RotateCcw,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { tasksApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { TaskItem } from '@/types'

export interface RoleTask {
  id: string
  title: string
  description: string
  role: string
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  points: number
  assigneeName?: string
}

const ROLE_META: Record<string, { label: string; badgeVariant: 'violet' | 'indigo' | 'emerald' | 'cyan' | 'amber' }> = {
  admin: { label: 'Administrator', badgeVariant: 'violet' },
  technical_lead: { label: 'Technical Lead', badgeVariant: 'violet' },
  software_developer: { label: 'Software Developer', badgeVariant: 'indigo' },
  qa_engineer: { label: 'QA Engineer', badgeVariant: 'emerald' },
  devops_engineer: { label: 'DevOps Engineer', badgeVariant: 'cyan' },
  project_manager: { label: 'Project Manager', badgeVariant: 'amber' },
  employee: { label: 'Team Member', badgeVariant: 'indigo' },
}

const DEFAULT_ROLE_TASKS: Record<string, RoleTask[]> = {
  admin: [
    {
      id: 'scrum_admin_1',
      title: 'Enterprise RBAC & Security Audit Compliance Signoff',
      description: 'Review access privileges, API key rotation policies, and export SOC2 compliance audit log.',
      role: 'admin',
      status: 'todo',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_admin_2',
      title: 'Deploy Multi-Agent AI Mesh Infrastructure & Tool Bindings',
      description: 'Supervise runtime cluster deployment for Google ADK and specialist agent mesh orchestration.',
      role: 'admin',
      status: 'in_progress',
      priority: 'critical',
      points: 8,
    },
    {
      id: 'scrum_admin_3',
      title: 'Corporate Identity Provider (IdP) & SSO Federation Config',
      description: 'Configured SAML 2.0 / OIDC provider mappings for enterprise single sign-on.',
      role: 'admin',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_admin_4',
      title: 'Q4 Technical Roadmap & Resource Allocation Review',
      description: 'Aligned engineering velocity targets and cloud infrastructure budget across squads.',
      role: 'admin',
      status: 'done',
      priority: 'high',
      points: 5,
    },
  ],
  technical_lead: [
    {
      id: 'scrum_tl_1',
      title: 'Design GraphQL Gateway Schema for Multi-Agent Task Synchronization',
      description: 'Architect federation schemas for real-time state sync across frontend and backend services.',
      role: 'technical_lead',
      status: 'todo',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_tl_2',
      title: 'Implement JWT refresh token rotation with atomic invalidation',
      description: 'Secure token rotation mechanism preventing replay attacks on API gateway.',
      role: 'technical_lead',
      status: 'in_progress',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_tl_3',
      title: 'Finalize OpenAPI 3.1 documentation for internal microservices',
      description: 'Align API spec models with Pydantic v2 schemas across all backend routes.',
      role: 'technical_lead',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_tl_4',
      title: 'Code review & merge gate for Google ADK streaming runtime',
      description: 'Audited specialist agent tool execution handlers and error recovery loops.',
      role: 'technical_lead',
      status: 'done',
      priority: 'medium',
      points: 2,
    },
  ],
  qa_engineer: [
    {
      id: 'scrum_qa_1',
      title: 'Automated Playwright regression test suite for meeting scheduling',
      description: 'Write end-to-end tests for calendar collision detection and instant auto-rescheduling.',
      role: 'qa_engineer',
      status: 'todo',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_qa_2',
      title: 'Cross-browser validation of theme contrast and accessibility standards',
      description: 'Verify WCAG AAA contrast compliance across Dark, Light, and System themes in My Learnings.',
      role: 'qa_engineer',
      status: 'in_progress',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_qa_3',
      title: 'Security exception verification for staging SSL wildcard certificates',
      description: 'Validated 14-day staging wildcard certificate deployment in isolated test cluster.',
      role: 'qa_engineer',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_qa_4',
      title: 'Validate WebSocket reconnection handling during network interruption',
      description: 'Verified seamless reconnection and message replay on simulated offline state.',
      role: 'qa_engineer',
      status: 'done',
      priority: 'low',
      points: 2,
    },
  ],
  software_developer: [
    {
      id: 'scrum_dev_1',
      title: 'Implement real-time WebSocket reconnect logic with exponential backoff',
      description: 'Ensure transparent live channel recovery without losing message state or typing presence.',
      role: 'software_developer',
      status: 'todo',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_dev_2',
      title: 'Build calendar collision detection and instant reschedule prompts',
      description: 'Calculate scheduling conflicts dynamically and notify attendees with alternate time slots.',
      role: 'software_developer',
      status: 'in_progress',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_dev_3',
      title: 'Integrate responsive design tokens and high-contrast theme switcher',
      description: 'Replaced hardcoded color styles with reactive CSS variables for seamless theme switching.',
      role: 'software_developer',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_dev_4',
      title: 'Unit test coverage for role-based onboarding journey progress',
      description: 'Wrote unit tests ensuring completion percentage calculations remain accurate.',
      role: 'software_developer',
      status: 'done',
      priority: 'low',
      points: 2,
    },
  ],
  devops_engineer: [
    {
      id: 'scrum_ops_1',
      title: 'Kubernetes HPA autoscaling policies for inference proxy pods',
      description: 'Configure resource thresholds and target CPU/memory metrics for auto-scaling.',
      role: 'devops_engineer',
      status: 'todo',
      priority: 'high',
      points: 5,
    },
    {
      id: 'scrum_ops_2',
      title: 'Deploy Prometheus + Grafana telemetry dashboard for API latency',
      description: 'Set up real-time p95 and p99 request latency monitoring for backend microservices.',
      role: 'devops_engineer',
      status: 'in_progress',
      priority: 'critical',
      points: 5,
    },
    {
      id: 'scrum_ops_3',
      title: 'Zero-downtime blue/green deployment pipeline for staging cluster',
      description: 'Configured automated canary testing and rolling updates via GitHub Actions.',
      role: 'devops_engineer',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_ops_4',
      title: 'Automated secret rotation in HashiCorp Vault',
      description: 'Scheduled weekly automated rotation for database credentials and service tokens.',
      role: 'devops_engineer',
      status: 'done',
      priority: 'medium',
      points: 3,
    },
  ],
  project_manager: [
    {
      id: 'scrum_pm_1',
      title: 'Sprint 43 backlog grooming and dependency mapping across squads',
      description: 'Coordinate deliverables and priority milestones with Tech Lead and Product Stakeholders.',
      role: 'project_manager',
      status: 'todo',
      priority: 'high',
      points: 3,
    },
    {
      id: 'scrum_pm_2',
      title: 'Daily standup blocker resolution and cross-team coordination',
      description: 'Facilitate async blocker resolution and resource reallocations for Sprint 42.',
      role: 'project_manager',
      status: 'in_progress',
      priority: 'medium',
      points: 2,
    },
    {
      id: 'scrum_pm_3',
      title: 'Sprint 42 milestone demo sign-off with enterprise stakeholders',
      description: 'Presented completed AI Workspace features and secured formal sign-off.',
      role: 'project_manager',
      status: 'done',
      priority: 'high',
      points: 3,
    },
    {
      id: 'scrum_pm_4',
      title: 'Review and approve associate onboarding curriculum tracks',
      description: 'Signed off on course progression requests for newly onboarded engineers.',
      role: 'project_manager',
      status: 'done',
      priority: 'low',
      points: 2,
    },
  ],
  employee: [
    {
      id: 'scrum_emp_1',
      title: 'Complete 30-day compliance documentation and digital NDA signatures',
      description: 'Verify identity documents and submit required HR agreements for digital filing.',
      role: 'employee',
      status: 'todo',
      priority: 'high',
      points: 2,
    },
    {
      id: 'scrum_emp_2',
      title: 'Review role curriculum modules and schedule introductory 1:1s',
      description: 'Progress through assigned role track and meet with team lead and assigned onboarding buddy.',
      role: 'employee',
      status: 'in_progress',
      priority: 'medium',
      points: 3,
    },
    {
      id: 'scrum_emp_3',
      title: 'Workspace environment setup and credentials verification',
      description: 'Configured local development tools, SSO credentials, and team communication channels.',
      role: 'employee',
      status: 'done',
      priority: 'low',
      points: 2,
    },
  ],
}

const KANBAN_LANES = [
  { id: 'todo', label: 'To Do', description: 'Queued for current sprint' },
  { id: 'in_progress', label: 'In Progress', description: 'Actively in development' },
  { id: 'done', label: 'Done', description: 'Verified and completed' },
] as const

export function ScrumPage() {
  const { user } = useAuth()
  const userRole = (user?.role || 'software_developer').toLowerCase()
  const [selectedRole, setSelectedRole] = useState<string>(userRole)
  const [roleTasks, setRoleTasks] = useState<RoleTask[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showStandupModal, setShowStandupModal] = useState(false)

  // New task form state
  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newPoints, setNewPoints] = useState('3')
  const [newPriority, setNewPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium')
  const [savingTask, setSavingTask] = useState(false)

  // Standup modal state
  const [standupDone, setStandupDone] = useState('Reviewed current sprint role tasks and verified test coverage.')
  const [standupNext, setStandupNext] = useState('Focusing on role-based deliverables and meeting coordination.')
  const [standupBlockers, setStandupBlockers] = useState('No blockers.')
  const [standupSubmitted, setStandupSubmitted] = useState(false)

  // Keep selectedRole synced when user profile changes
  useEffect(() => {
    if (user?.role) {
      setSelectedRole(user.role.toLowerCase())
    }
  }, [user?.role])

  // Load and merge tasks
  const loadTasks = async () => {
    setLoading(true)
    try {
      // Fetch backend tasks
      const res = await tasksApi.listTasks()
      const apiTasks: TaskItem[] = res.items || []

      // Get curated 3-4 role tasks for the active role
      const defaults = DEFAULT_ROLE_TASKS[selectedRole] || DEFAULT_ROLE_TASKS.software_developer

      // Map API tasks for current user/role if any exist
      const matchingApiTasks: RoleTask[] = apiTasks
        .filter((t) => {
          const hasRoleTag = t.tags?.some((tag) => tag.toLowerCase() === `role:${selectedRole}`)
          return t.assignee_id === user?.id || hasRoleTag
        })
        .slice(0, 2)
        .map((t) => {
          const rawStatus = (t.status || 'todo').toLowerCase()
          const status: 'todo' | 'in_progress' | 'done' =
            rawStatus === 'done' || rawStatus === 'completed'
              ? 'done'
              : rawStatus === 'in_progress' || rawStatus === 'in_review' || rawStatus === 'qa_testing'
              ? 'in_progress'
              : 'todo'

          const pointsTag = t.tags?.find((tag) => tag.startsWith('points:'))?.replace('points:', '')

          return {
            id: t.id,
            title: t.title,
            description: t.description || '',
            role: selectedRole,
            status,
            priority: (t.priority as any) || 'medium',
            points: pointsTag ? parseInt(pointsTag, 10) || 3 : 3,
            assigneeName: user?.name,
          }
        })

      // Combine matching API tasks with defaults, maintaining exactly 3-4 tasks
      const combined = [...matchingApiTasks]
      for (const def of defaults) {
        if (!combined.some((c) => c.title.toLowerCase() === def.title.toLowerCase())) {
          combined.push({
            ...def,
            assigneeName: user?.name || def.assigneeName,
          })
        }
        if (combined.length >= 4) break
      }

      setRoleTasks(combined.slice(0, 4))
    } catch {
      // Fallback cleanly to default role tasks (3-4 items)
      const defaults = DEFAULT_ROLE_TASKS[selectedRole] || DEFAULT_ROLE_TASKS.software_developer
      setRoleTasks(defaults.map((d) => ({ ...d, assigneeName: user?.name })))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [selectedRole])

  // Move task status forward or backward
  const handleMoveStatus = (taskId: string, targetStatus: 'todo' | 'in_progress' | 'done') => {
    setRoleTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: targetStatus } : t))
    )
    // Optional backend sync
    tasksApi.updateTaskStatus(taskId, targetStatus).catch(() => {})
  }

  // Create a new role task
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    setSavingTask(true)

    const newTask: RoleTask = {
      id: `task_custom_${Date.now()}`,
      title: newTitle.trim(),
      description: newDescription.trim() || `Role task for ${ROLE_META[selectedRole]?.label || selectedRole}`,
      role: selectedRole,
      status: 'todo',
      priority: newPriority,
      points: parseInt(newPoints, 10) || 3,
      assigneeName: user?.name,
    }

    // Try posting to backend
    try {
      await tasksApi.createTask({
        title: newTask.title,
        description: newTask.description,
        assignee_id: user?.id,
        priority: newTask.priority,
        tags: [`role:${selectedRole}`, `points:${newTask.points}`, 'sprint:Sprint 42'],
      })
    } catch {
      // Non-blocking in UI
    }

    // Replace the first 'todo' task or prepend to keep at 3-4 role tasks
    setRoleTasks((prev) => {
      const nonTodo = prev.filter((t) => t.status !== 'todo')
      return [newTask, ...nonTodo].slice(0, 4)
    })

    setNewTitle('')
    setNewDescription('')
    setShowCreateModal(false)
    setSavingTask(false)
  }

  const roleMeta = ROLE_META[selectedRole] || ROLE_META.software_developer
  const completedCount = useMemo(() => roleTasks.filter((t) => t.status === 'done').length, [roleTasks])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* ─── 1. SIMPLIFIED HEADER ────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-5">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-violet-500/15 via-purple-500/15 to-indigo-500/15 border border-violet-200 dark:border-violet-500/30 flex items-center justify-center text-violet-600 dark:text-violet-400">
              <CheckSquare className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  Scrum Board
                </h1>
                <Badge variant={roleMeta.badgeVariant} size="sm">
                  {roleMeta.label}
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-0.5">
                Showing 3–4 focused role tasks for Sprint 42 • {completedCount} of {roleTasks.length} tasks completed
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Role Switcher Preview */}
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="text-xs h-9 px-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-violet-500 font-medium"
              title="Switch role view"
            >
              <option value="admin">Admin / CTO View</option>
              <option value="technical_lead">Tech Lead View</option>
              <option value="software_developer">Developer View</option>
              <option value="qa_engineer">QA Engineer View</option>
              <option value="devops_engineer">DevOps View</option>
              <option value="project_manager">Project Manager View</option>
            </select>

            <Button
              variant="secondary"
              size="sm"
              onClick={loadTasks}
              disabled={loading}
              className="gap-2 text-xs h-9 px-3.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-violet-500 dark:text-violet-400 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowStandupModal(true)}
              className="gap-2 text-xs h-9 px-3.5 border-amber-500/20 hover:border-amber-500/40 text-amber-700 dark:text-amber-300"
            >
              <Users className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              Daily Standup
            </Button>

            <Button
              size="sm"
              variant="gemini"
              onClick={() => setShowCreateModal(true)}
              className="gap-2 text-xs h-9 px-4 rounded-xl shadow-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Task
            </Button>
          </div>
        </div>

        {/* ─── 2. ACTIVE SPRINT OVERVIEW STRIP ─────────────────────────── */}
        <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-default)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-600 dark:text-violet-400">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--text-primary)]">Sprint 42: Core AI Mesh & Role Operations</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 font-semibold">
                  Active Sprint
                </span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Current Role Track: <strong className="text-[var(--text-primary)]">{roleMeta.label}</strong> ({user?.name || 'Logged-in User'})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-muted)]">
            <span>Sprint Window: Oct 14 – Oct 27</span>
            <span>•</span>
            <span className="text-violet-600 dark:text-violet-400 font-semibold">3 Days Left</span>
          </div>
        </div>

        {/* ─── 3. SIMPLIFIED 3-COLUMN KANBAN BOARD ─────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {KANBAN_LANES.map((lane) => {
            const laneTasks = roleTasks.filter((t) => t.status === lane.id)

            return (
              <div
                key={lane.id}
                className="flex flex-col rounded-2xl bg-[var(--bg-elevated)]/40 border border-[var(--border-subtle)] p-4 min-h-[460px]"
              >
                {/* Lane Header */}
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)]">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-[var(--text-primary)]">
                        {lane.label}
                      </span>
                      <Badge variant="default" size="sm" className="font-mono text-[10px]">
                        {laneTasks.length}
                      </Badge>
                    </div>
                    <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">
                      {lane.description}
                    </span>
                  </div>
                </div>

                {/* Lane Task Cards */}
                <div className="space-y-3 flex-1 overflow-y-auto">
                  {laneTasks.length === 0 ? (
                    <div className="h-32 flex items-center justify-center text-center p-3 rounded-xl border border-dashed border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
                      No tasks in {lane.label}
                    </div>
                  ) : (
                    laneTasks.map((task) => (
                      <div
                        key={task.id}
                        className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-violet-500/40 shadow-xs transition-all space-y-3 group"
                      >
                        {/* Header: Badge & Points */}
                        <div className="flex items-center justify-between gap-1">
                          <Badge variant={roleMeta.badgeVariant} size="sm" className="text-[10px]">
                            {roleMeta.label}
                          </Badge>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                              {task.points} pts
                            </span>
                            <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                              task.priority === 'critical'
                                ? 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/30'
                                : task.priority === 'high'
                                ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30'
                                : 'bg-zinc-500/10 text-[var(--text-muted)]'
                            }`}>
                              {task.priority}
                            </span>
                          </div>
                        </div>

                        {/* Title & Description */}
                        <div>
                          <h4 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] leading-snug">
                            {task.title}
                          </h4>
                          {task.description && (
                            <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">
                              {task.description}
                            </p>
                          )}
                        </div>

                        {/* Footer & Actions */}
                        <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
                          <div className="flex items-center gap-1.5 text-[var(--text-muted)]">
                            <div className="h-5 w-5 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center text-[9px] font-bold text-violet-700 dark:text-violet-300">
                              {(task.assigneeName || user?.name || 'U')[0]}
                            </div>
                            <span className="truncate max-w-[100px] text-[11px]">
                              {task.assigneeName || user?.name || 'You'}
                            </span>
                          </div>

                          {/* Action Buttons */}
                          {lane.id === 'todo' && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleMoveStatus(task.id, 'in_progress')}
                              className="text-[11px] h-6 px-2.5 text-violet-700 dark:text-violet-300 hover:bg-violet-500/10 border-violet-500/30"
                            >
                              Start <ArrowRight className="h-3 w-3 ml-1" />
                            </Button>
                          )}

                          {lane.id === 'in_progress' && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleMoveStatus(task.id, 'done')}
                              className="text-[11px] h-6 px-2.5 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 border-emerald-500/30"
                            >
                              Complete <CheckCircle2 className="h-3 w-3 ml-1" />
                            </Button>
                          )}

                          {lane.id === 'done' && (
                            <div className="flex items-center gap-1.5">
                              <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                                <CheckCircle2 className="h-3.5 w-3.5" /> Done
                              </span>
                              <button
                                onClick={() => handleMoveStatus(task.id, 'in_progress')}
                                className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                title="Reopen task"
                              >
                                <RotateCcw className="h-3 w-3" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* ─── 4. MODAL: CREATE ROLE-BASED SCRUM TASK ──────────────────── */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-lg p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-600 dark:text-violet-400">
                    <CheckSquare className="h-4 w-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-[var(--text-primary)]">Add Role Task</h2>
                    <p className="text-xs text-[var(--text-muted)]">Create a focused task for {roleMeta.label}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Task Title *</label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Implement calendar collision check and auto-reschedule"
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Story Points</label>
                    <select
                      value={newPoints}
                      onChange={(e) => setNewPoints(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-violet-500"
                    >
                      <option value="1">1 Point (Trivial)</option>
                      <option value="2">2 Points (Small)</option>
                      <option value="3">3 Points (Medium)</option>
                      <option value="5">5 Points (Complex)</option>
                      <option value="8">8 Points (Epic)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Priority</label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(e.target.value as any)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-violet-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Description & Scope</label>
                  <textarea
                    rows={2}
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    placeholder="Brief description of the deliverables and verification steps..."
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-[var(--border-default)]">
                  <Button type="button" variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="gemini" size="sm" loading={savingTask}>
                    Create Task
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* ─── 5. MODAL: DAILY STANDUP LOG ─────────────────────────────── */}
        {showStandupModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-lg p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-600 dark:text-amber-400">
                    <Users className="h-4 w-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-[var(--text-primary)]">Daily Standup</h2>
                    <p className="text-xs text-[var(--text-muted)]">Async standup sync for Sprint 42</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowStandupModal(false)}
                  className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {standupSubmitted ? (
                <div className="p-6 text-center space-y-3">
                  <div className="h-12 w-12 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="h-6 w-6" />
                  </div>
                  <h3 className="text-sm font-bold text-[var(--text-primary)]">Standup Shared with Team!</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Your daily check-in has been logged for Sprint 42.
                  </p>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      setStandupSubmitted(false)
                      setShowStandupModal(false)
                    }}
                    className="mt-3 text-xs"
                  >
                    Done
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                      1. Accomplished Yesterday
                    </label>
                    <textarea
                      rows={2}
                      value={standupDone}
                      onChange={(e) => setStandupDone(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                      2. Working on Today
                    </label>
                    <textarea
                      rows={2}
                      value={standupNext}
                      onChange={(e) => setStandupNext(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                      3. Blockers or Dependencies
                    </label>
                    <textarea
                      rows={2}
                      value={standupBlockers}
                      onChange={(e) => setStandupBlockers(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-2 border-t border-[var(--border-default)]">
                    <Button type="button" variant="ghost" size="sm" onClick={() => setShowStandupModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="gemini"
                      onClick={() => setStandupSubmitted(true)}
                    >
                      Publish Standup Check-in
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
