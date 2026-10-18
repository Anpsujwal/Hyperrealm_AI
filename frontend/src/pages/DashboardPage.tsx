import { useState, useEffect, useMemo } from 'react'
import {
  CheckSquare,
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
  meetingsApi,
  learningApi,
  knowledgeApi,
} from '@/lib/api'
import { formatISTTime } from '@/lib/utils'
import type {
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
          meetingsRes,
          learningRes,
          guidelinesRes,
        ] = await Promise.allSettled([
          meetingsApi.listMeetings(),
          learningApi.getLearningPaths(user?.role),
          knowledgeApi.listGuidelines(),
        ])

        if (!mounted) return

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

  // Filter exclusively for today's calls relevant to the logged-in user (present day only)
  const todayMeetings = useMemo(() => {
    const today = new Date()
    const todayYear = today.getFullYear()
    const todayMonth = today.getMonth()
    const todayDate = today.getDate()

    return meetings
      .filter((m) => {
        const isRelevant = !user?.id || m.organiser_id === user.id || m.attendee_ids?.includes(user.id)
        if (!isRelevant) return false

        const d = new Date(m.scheduled_at)
        return (
          d.getFullYear() === todayYear &&
          d.getMonth() === todayMonth &&
          d.getDate() === todayDate
        )
      })
      .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
  }, [meetings, user?.id])

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
        <div className="relative overflow-hidden rounded-3xl border border-[var(--border-default)] dark:border-zinc-800 bg-gradient-to-br from-indigo-50/50 via-[var(--bg-surface)] to-purple-50/30 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-950 p-6 sm:p-7 shadow-xs dark:shadow-none">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-400/10 via-purple-400/10 to-transparent dark:hidden rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
          
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)] leading-normal">
                  {greeting}, <span className="text-gemini inline-block py-0.5 px-0.5">{user?.name || 'there'}</span>
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
              <Link to="/app/knowledge">
                <Button size="sm" variant="secondary" className="gap-1.5 text-xs h-9 px-4 rounded-full">
                  <FileText className="h-3.5 w-3.5 text-indigo-400" />
                  Knowledge Hub
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* ─── 2. ESSENTIAL METRIC CARDS ───────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* AI Copilot */}
          <Link to="/app/chat" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-purple-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(155,114,207,0.2)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">AI Copilot</span>
                <div className="h-8 w-8 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 shadow-xs">
                  <Sparkles className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">Ready</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 truncate">
                Gemini 3.8 Flash • 4 Agents
              </p>
            </Card>
          </Link>

          {/* Knowledge & Guidelines */}
          <Link to="/app/knowledge" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-blue-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(66,133,244,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Company Policies</span>
                <div className="h-8 w-8 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 shadow-xs">
                  <FileText className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{guidelines.length}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 truncate">
                Authoritative Guidelines Active
              </p>
            </Card>
          </Link>

          {/* Today's Meetings */}
          <Link to="/app/meetings" className="block group">
            <Card className="p-5 rounded-2xl transition-all duration-200 group-hover:border-cyan-500/40 group-hover:shadow-[0_8px_24px_-4px_rgba(6,182,212,0.15)] group-hover:-translate-y-0.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Today&apos;s Calls</span>
                <div className="h-8 w-8 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-500 shadow-xs">
                  <Calendar className="h-4 w-4" />
                </div>
              </div>
              <p className="font-display text-3xl font-bold tracking-tight text-[var(--text-primary)]">{todayMeetings.length}</p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 truncate">
                {todayMeetings.length > 0 ? (
                  <span>Next: {todayMeetings[0].title}</span>
                ) : (
                  'No calls scheduled today'
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
        {/* ─── 3. FOCUSED 2-COLUMN SECTION ─────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* LEFT 2 COLUMNS: Today's Schedule & Active Sprint Overview */}
          <div className="lg:col-span-2 space-y-6">
            {/* Scheduled Calls & Calendar API Card */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-cyan-400" />
                    <CardTitle className="text-sm font-semibold">Today&apos;s Scheduled Calls & Meetings</CardTitle>
                    <Badge variant={todayMeetings.length > 0 ? 'cyan' : 'default'} size="sm">
                      {todayMeetings.length} today
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Calendar API Active
                    </span>
                    <Link
                      to="/app/meetings"
                      className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                    >
                      Calendar Hub <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-2.5">
                {todayMeetings.length > 0 ? (
                  todayMeetings.map((meeting) => (
                    <div
                      key={meeting.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-cyan-500/30 transition-all"
                    >
                      <div className="flex items-center gap-3 min-w-0 pr-2">
                        <div className="px-2.5 py-1.5 rounded-md bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[11px] font-mono text-cyan-400 font-semibold whitespace-nowrap">
                          {formatISTTime(meeting.scheduled_at, true)}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-semibold text-[var(--text-primary)] truncate">
                              {meeting.title}
                            </p>
                            {meeting.status === 'rescheduled' && (
                              <Badge variant="violet" size="sm" className="text-[9px] py-0 px-1.5">
                                Rescheduled
                              </Badge>
                            )}
                          </div>
                          <p className="text-[10px] text-[var(--text-muted)] flex items-center gap-2 mt-0.5">
                            <span>{meeting.duration_minutes} min duration</span>
                            <span>•</span>
                            <span className="text-indigo-400">Google Meet Ready</span>
                            {meeting.attendee_ids && meeting.attendee_ids.length > 0 && (
                              <>
                                <span>•</span>
                                <span>
                                  {meeting.attendee_ids.length} participant{meeting.attendee_ids.length > 1 ? 's' : ''}
                                </span>
                              </>
                            )}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant="cyan" size="sm" className="capitalize text-[10px]">
                          {meeting.type || 'Meeting'}
                        </Badge>
                        <Link to="/app/meetings">
                          <Button size="sm" variant="secondary" className="h-7 text-[11px] px-2.5 gap-1">
                            Join Call
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-6 text-center space-y-2">
                    <p className="text-xs font-medium text-[var(--text-secondary)]">
                      No calls scheduled for today.
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      Your schedule is clear for today. You can schedule a new call in the Calendar Hub.
                    </p>
                    <Link to="/app/meetings">
                      <Button size="sm" variant="secondary" className="text-xs h-7 px-3 mt-1">
                        Open Calendar Hub
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Sprint & Scrum Tracker Card */}
            <Card className="border-[var(--border-default)]">
              <CardHeader className="pb-3 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-violet-400" />
                    <CardTitle className="text-sm font-semibold">Active Sprint & Scrum Highlights</CardTitle>
                    <Badge variant="violet" size="sm">
                      Sprint 42 Active
                    </Badge>
                  </div>
                  <Link
                    to="/app/scrum"
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
                  >
                    Open Scrum Board <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-4">
                <div className="p-3.5 rounded-xl bg-gradient-to-r from-violet-50/80 via-purple-50/40 to-transparent dark:from-zinc-900 dark:via-zinc-900/60 dark:to-transparent border border-violet-200/80 dark:border-zinc-800">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div>
                      <h4 className="text-xs font-bold text-[var(--text-primary)] flex items-center gap-2">
                        Sprint 42: AI Workspace & Multi-Agent Mesh
                      </h4>
                      <p className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                        Sprint Goal: Deliver full Google ADK runtime, role-based tasks, and enterprise meetings calendar.
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-[11px] font-mono font-semibold text-violet-400">
                        34 / 38 Story Points
                      </span>
                      <p className="text-[10px] text-[var(--text-muted)]">Velocity target: 89%</p>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-[var(--text-muted)]">
                      <span>Sprint Progress</span>
                      <span className="font-semibold text-violet-400">89%</span>
                    </div>
                    <div className="h-2 w-full bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-500" style={{ width: '89%' }} />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
                  <div className="p-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                    <p className="text-[10px] text-[var(--text-muted)]">To Do</p>
                    <p className="text-sm font-bold text-[var(--text-primary)] mt-0.5">3 Tasks</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                    <p className="text-[10px] text-amber-400">In Progress</p>
                    <p className="text-sm font-bold text-[var(--text-primary)] mt-0.5">4 Tasks</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                    <p className="text-[10px] text-cyan-400">Code Review</p>
                    <p className="text-sm font-bold text-[var(--text-primary)] mt-0.5">2 Tasks</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-center">
                    <p className="text-[10px] text-emerald-400">Done</p>
                    <p className="text-sm font-bold text-[var(--text-primary)] mt-0.5">18 Tasks</p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <p className="text-[11px] text-[var(--text-muted)]">
                    Role-assigned sprint tasks and daily standup ceremonies
                  </p>
                  <Link to="/app/scrum">
                    <Button size="sm" variant="gemini" className="h-7 text-xs px-3">
                      View Scrum Details
                    </Button>
                  </Link>
                </div>
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
