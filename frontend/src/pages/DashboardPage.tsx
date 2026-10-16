import { useState, useEffect, useMemo } from 'react'
import {
  CheckSquare,
  AlertCircle,
  Calendar,
  GraduationCap,
  Clock,
  ArrowRight,
  Sparkles,
  ChevronRight,
  CheckCircle2,
  FileText,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/contexts/AuthContext'
import {
  tasksApi,
  meetingsApi,
  learningApi,
  knowledgeApi,
} from '@/lib/api'
import type {
  TaskItem,
  ApprovalItem,
  MeetingItem,
  LearningItem,
  GuidelineItem,
} from '@/types'

const roleBadgeVariants: Record<string, 'indigo' | 'violet' | 'cyan' | 'emerald' | 'amber' | 'rose'> = {
  admin: 'rose',
  technical_lead: 'violet',
  project_manager: 'amber',
  software_developer: 'indigo',
  devops_engineer: 'cyan',
  qa_engineer: 'emerald',
  employee: 'indigo',
}

const formatRoleTitle = (role?: string) => {
  if (!role) return 'Team Member'
  return role
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function DashboardPage() {
  const { user } = useAuth()

  // State
  const [loading, setLoading] = useState(true)
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [meetings, setMeetings] = useState<MeetingItem[]>([])
  const [learningItems, setLearningItems] = useState<LearningItem[]>([])
  const [guidelines, setGuidelines] = useState<GuidelineItem[]>([])
  const [learningRole, setLearningRole] = useState('')

  const greeting = useMemo(() => {
    const hour = new Date().getHours()
    return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  }, [])

  const formattedDate = useMemo(() => {
    return new Date().toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    })
  }, [])

  useEffect(() => {
    let mounted = true

    const loadDashboardData = async () => {
      try {
        setLoading(true)
        const [
          tasksRes,
          approvalsRes,
          meetingsRes,
          learningRes,
          guidelinesRes,
        ] = await Promise.allSettled([
          tasksApi.listTasks(),
          tasksApi.listApprovals(),
          meetingsApi.listMeetings(),
          learningApi.getLearningPaths(user?.role),
          knowledgeApi.listGuidelines(),
        ])

        if (!mounted) return

        if (tasksRes.status === 'fulfilled') {
          setTasks(tasksRes.value.items || [])
        }
        if (approvalsRes.status === 'fulfilled') {
          setApprovals(approvalsRes.value.items || [])
        }
        if (meetingsRes.status === 'fulfilled') {
          setMeetings(meetingsRes.value.items || [])
        }
        if (learningRes.status === 'fulfilled') {
          setLearningItems(learningRes.value.items || [])
          setLearningRole(learningRes.value.role || user?.role || '')
        }
        if (guidelinesRes.status === 'fulfilled') {
          setGuidelines(guidelinesRes.value.items || [])
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadDashboardData()

    return () => {
      mounted = false
    }
  }, [user?.role])

  // Calculated metrics
  const activeTasks = useMemo(() => tasks.filter((t) => t.status !== 'done'), [tasks])
  const completedTasks = useMemo(() => tasks.filter((t) => t.status === 'done'), [tasks])
  const pendingApprovals = useMemo(() => approvals.filter((a) => a.status === 'pending'), [approvals])

  // Learning statistics & current next module
  const learningStats = useMemo(() => {
    const total = learningItems.length
    if (total === 0) return { pct: 0, completed: 0, total: 0 }
    const completed = learningItems.filter(
      (i) => i.status === 'completed' || (i.progress_pct && i.progress_pct >= 100)
    ).length
    const avgPct = Math.round(
      learningItems.reduce((acc, curr) => acc + (curr.progress_pct || 0), 0) / total
    )
    return { pct: avgPct, completed, total }
  }, [learningItems])

  const nextLearningItem = useMemo(() => {
    return learningItems.find(
      (item) => item.status !== 'completed' && (!item.progress_pct || item.progress_pct < 100)
    )
  }, [learningItems])

  // Sorted upcoming meetings
  const upcomingMeetings = useMemo(() => {
    return [...meetings]
      .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
      .slice(0, 3)
  }, [meetings])

  // Focus tasks (active tasks first, sorted by due date)
  const focusTasks = useMemo(() => {
    const sorted = [...activeTasks].sort((a, b) => {
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
    })
    return sorted.slice(0, 4)
  }, [activeTasks])

  // Toggle quick task completion
  const handleToggleTask = async (taskId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'done' ? 'in_progress' : 'done'
    try {
      await tasksApi.updateTaskStatus(taskId, newStatus)
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      )
    } catch (err) {
      console.error('Failed to toggle task:', err)
    }
  }

  const userRoleKey = (user?.role || 'employee').toLowerCase()
  const roleColorVariant = roleBadgeVariants[userRoleKey] || 'indigo'

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="flex flex-col items-center gap-3">
          <div className="h-7 w-7 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <p className="text-xs text-[var(--text-muted)]">Loading your workspace...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* ─── 1. GEMINI-INSPIRED HERO HEADER ─────────────────────────── */}
        <div className="relative overflow-hidden rounded-3xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-6 sm:p-7 shadow-sm">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-500/10 via-purple-500/10 to-transparent rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
          
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
                  {greeting}, <span className="text-gemini">{user?.name || 'there'}</span>
                </h1>
                <Badge variant={roleColorVariant} size="sm">
                  {formatRoleTitle(user?.role)}
                </Badge>
                {user?.department && (
                  <span className="text-xs text-[var(--text-muted)] font-medium">
                    • {user.department}
                  </span>
                )}
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1.5 flex items-center gap-2">
                <span>{formattedDate}</span>
                <span>•</span>
                <span>Workspace overview & active intelligence priorities</span>
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link to="/app/chat">
                <Button size="sm" variant="gemini" className="gap-2 text-xs h-9 px-4 rounded-full shadow-md">
                  <Sparkles className="h-3.5 w-3.5" />
                  Ask Copilot
                </Button>
              </Link>
              <Link to="/app/tasks">
                <Button size="sm" variant="secondary" className="gap-1.5 text-xs h-9 px-4 rounded-full">
                  <CheckSquare className="h-3.5 w-3.5 text-purple-400" />
                  View Tasks
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* ─── 2. ESSENTIAL METRIC CARDS ───────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Active Tasks */}
          <Link to="/app/tasks" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-blue-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(66,133,244,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Active Tasks</span>
                <div className="h-8 w-8 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 shadow-xs">
                  <CheckSquare className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{activeTasks.length}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 truncate">
                {completedTasks.length} of {tasks.length} completed
              </p>
            </Card>
          </Link>

          {/* Pending Approvals */}
          <Link to="/app/tasks" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-amber-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(245,158,11,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Approvals</span>
                <div className="h-8 w-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500 shadow-xs">
                  <AlertCircle className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{pendingApprovals.length}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5">
                {pendingApprovals.length > 0 ? (
                  <span className="text-amber-500 font-medium">Requires sign-off</span>
                ) : (
                  'All caught up'
                )}
              </p>
            </Card>
          </Link>

          {/* Today's Meetings */}
          <Link to="/app/meetings" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-purple-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(155,114,207,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Upcoming Events</span>
                <div className="h-8 w-8 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-500 shadow-xs">
                  <Calendar className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{meetings.length}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 truncate">
                {upcomingMeetings.length > 0 ? (
                  <span>Next: {upcomingMeetings[0].title}</span>
                ) : (
                  'No events scheduled'
                )}
              </p>
            </Card>
          </Link>

          {/* Learning Curriculum */}
          <Link to="/app/learning" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-emerald-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(16,185,129,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Learning Path</span>
                <div className="h-8 w-8 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 shadow-xs">
                  <GraduationCap className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{learningStats.pct}%</p>
              <div className="mt-2.5 h-1.5 w-full bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-300"
                  style={{ width: `${learningStats.pct}%` }}
                />
              </div>
            </Card>
          </Link>
        </div>

        {/* ─── 3. FOCUSED 2-COLUMN SECTION ─────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* LEFT 2 COLUMNS: Priority Tasks & Today's Schedule */}
          <div className="lg:col-span-2 space-y-6">
            {/* Priority Tasks Card */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-indigo-400" />
                    <CardTitle className="text-sm font-semibold">Priority Tasks</CardTitle>
                    <Badge variant="indigo" size="sm">
                      {activeTasks.length} active
                    </Badge>
                  </div>
                  <Link
                    to="/app/tasks"
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                  >
                    View all <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-2.5">
                {/* Pending approvals reminder if any */}
                {pendingApprovals.length > 0 && (
                  <Link
                    to="/app/tasks"
                    className="flex items-center justify-between p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs hover:bg-amber-500/15 transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />
                      <span className="font-medium text-amber-300">
                        {pendingApprovals.length} approval request{pendingApprovals.length > 1 ? 's' : ''} awaiting your review
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold text-amber-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                      Review <ChevronRight className="h-3 w-3" />
                    </span>
                  </Link>
                )}

                {/* Tasks List */}
                {focusTasks.length > 0 ? (
                  focusTasks.map((task) => {
                    const isOverdue =
                      task.due_date && new Date(task.due_date).getTime() < Date.now()
                    return (
                      <div
                        key={task.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-indigo-500/30 transition-all"
                      >
                        <div className="flex items-center gap-3 min-w-0 pr-3">
                          <button
                            onClick={() => handleToggleTask(task.id, task.status)}
                            className="h-4.5 w-4.5 rounded border border-[var(--border-strong)] hover:border-indigo-400 flex items-center justify-center text-transparent hover:text-indigo-400 transition-colors flex-shrink-0"
                            title="Mark as done"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          </button>
                          <div className="min-w-0">
                            <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                              {task.title}
                            </p>
                            {task.due_date && (
                              <p
                                className={`text-[10px] mt-0.5 flex items-center gap-1 ${
                                  isOverdue ? 'text-rose-400 font-semibold' : 'text-[var(--text-muted)]'
                                }`}
                              >
                                <Clock className="h-2.5 w-2.5" />
                                {isOverdue ? 'Overdue • ' : 'Due '}
                                {new Date(task.due_date).toLocaleDateString([], {
                                  month: 'short',
                                  day: 'numeric',
                                })}
                              </p>
                            )}
                          </div>
                        </div>

                        <Badge
                          variant={
                            task.priority === 'urgent' || task.priority === 'high'
                              ? 'rose'
                              : 'indigo'
                          }
                          size="sm"
                          className="capitalize text-[10px]"
                        >
                          {task.priority}
                        </Badge>
                      </div>
                    )
                  })
                ) : (
                  <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                    No active tasks right now. You are all caught up!
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Upcoming Schedule Card */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-cyan-400" />
                    <CardTitle className="text-sm font-semibold">Today&apos;s Schedule</CardTitle>
                    <Badge variant="cyan" size="sm">
                      {meetings.length} scheduled
                    </Badge>
                  </div>
                  <Link
                    to="/app/meetings"
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                  >
                    All meetings <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-2">
                {upcomingMeetings.length > 0 ? (
                  upcomingMeetings.map((meeting) => (
                    <div
                      key={meeting.id}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-cyan-500/30 transition-all"
                    >
                      <div className="flex items-center gap-3 min-w-0 pr-2">
                        <div className="px-2 py-1 rounded bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[10px] font-mono text-cyan-400 font-semibold whitespace-nowrap">
                          {new Date(meeting.scheduled_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                            {meeting.title}
                          </p>
                          <p className="text-[10px] text-[var(--text-muted)]">
                            {meeting.duration_minutes} min duration
                          </p>
                        </div>
                      </div>

                      <Badge variant="cyan" size="sm" className="capitalize text-[10px]">
                        {meeting.type || 'Meeting'}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                    No scheduled meetings for today.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* RIGHT 1 COLUMN: Learning Journey + Company Updates */}
          <div className="space-y-6">
            {/* Learning Path Card */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-4 w-4 text-emerald-400" />
                    <CardTitle className="text-sm font-semibold">My Learning</CardTitle>
                  </div>
                  <Link
                    to="/app/learning"
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                  >
                    View <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-4">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--text-secondary)]">Curriculum Progress</span>
                    <span className="font-semibold text-emerald-400">{learningStats.pct}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-[var(--bg-overlay)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                      style={{ width: `${learningStats.pct}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-[var(--text-muted)] pt-0.5">
                    {learningStats.completed} of {learningStats.total} modules cleared for{' '}
                    <span className="font-medium text-[var(--text-secondary)]">
                      {formatRoleTitle(learningRole || user?.role)}
                    </span>
                  </p>
                </div>

                {nextLearningItem ? (
                  <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                        Up Next
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                        <Clock className="h-2.5 w-2.5" />
                        {nextLearningItem.estimated_minutes}m
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
                      {nextLearningItem.title}
                    </p>
                    <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2">
                      {nextLearningItem.description}
                    </p>
                    <div className="pt-1">
                      <Link to="/app/learning">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full h-7 text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 justify-between"
                        >
                          <span>Continue Module</span>
                          <ChevronRight className="h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
                    <p className="text-xs font-semibold text-emerald-300">All Modules Complete</p>
                    <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
                      You are up to date with your role curriculum.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Knowledge & Guidelines Updates */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-indigo-400" />
                    <CardTitle className="text-sm font-semibold">Knowledge Updates</CardTitle>
                  </div>
                  <Link
                    to="/app/knowledge"
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                  >
                    Hub <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-2.5">
                {guidelines.slice(0, 3).map((guide) => (
                  <Link
                    key={guide.id}
                    to="/app/knowledge"
                    className="block p-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-indigo-500/30 transition-all group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-medium text-[var(--text-primary)] group-hover:text-indigo-400 transition-colors truncate">
                        {guide.title}
                      </p>
                      <Badge variant="indigo" size="sm" className="text-[9px] py-0 px-1.5 flex-shrink-0">
                        {guide.version || 'v1.0'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)] mt-1">
                      <span className="capitalize">{guide.category || 'Standard'}</span>
                      <span>
                        {new Date(guide.updated_at || guide.created_at).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                  </Link>
                ))}

                {guidelines.length === 0 && (
                  <p className="text-xs text-[var(--text-muted)] py-4 text-center">
                    No recent guideline updates.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
