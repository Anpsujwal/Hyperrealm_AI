import { useState, useEffect, useMemo } from 'react'
import {
  GraduationCap,
  Clock,
  CheckCircle2,
  Play,
  RefreshCw,
  Search,
  Lock,
  Calendar,
  Check,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { learningApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { LearningItem } from '@/types'

const ROLE_OPTIONS = [
  { id: 'my_role', label: 'My Learning Track' },
  { id: 'qa_engineer', label: 'QA Engineer' },
  { id: 'software_developer', label: 'Software Developer' },
  { id: 'devops_engineer', label: 'DevOps Engineer' },
  { id: 'project_manager', label: 'Project Manager / Scrum' },
  { id: 'technical_lead', label: 'Technical Lead' },
  { id: 'employee', label: 'New Employee Onboarding' },
]

const categoryColors: Record<string, 'indigo' | 'violet' | 'cyan' | 'emerald' | 'amber'> = {
  engineering: 'indigo',
  security: 'emerald',
  devops: 'cyan',
  process: 'violet',
  hr: 'amber',
}

export function MyLearningPage() {
  const { user } = useAuth()
  const [selectedRoleTab, setSelectedRoleTab] = useState<string>('my_role')
  const [learningItems, setLearningItems] = useState<LearningItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'mandatory' | 'in_progress' | 'completed' | 'not_started'>('all')
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)

  const effectiveRole = useMemo(() => {
    if (selectedRoleTab === 'my_role') {
      return user?.role || 'software_developer'
    }
    return selectedRoleTab
  }, [selectedRoleTab, user])

  const loadLearningData = async () => {
    setLoading(true)
    try {
      const res = await learningApi.getLearningPaths(effectiveRole)
      setLearningItems(res.items || [])
    } catch (err) {
      console.error('Failed to load learning path:', err)
      // Fallback to listResources
      try {
        const fallback = await learningApi.listResources()
        setLearningItems(fallback.items || [])
      } catch {
        // use empty
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLearningData()
  }, [effectiveRole])

  // Progress update handler
  const handleUpdateProgress = async (resourceId: string, newStatus: string, pct: number) => {
    setActionInProgress(resourceId)
    try {
      await learningApi.updateProgress(resourceId, newStatus, pct)
      // Optimistically update locally
      setLearningItems((prev) =>
        prev.map((item) =>
          item.id === resourceId
            ? {
                ...item,
                status: newStatus,
                progress_pct: pct,
                completed_at: newStatus === 'completed' ? new Date().toISOString() : item.completed_at,
              }
            : item
        )
      )
    } catch (err) {
      console.error('Failed to update progress:', err)
      await loadLearningData()
    } finally {
      setActionInProgress(null)
    }
  }

  // Summary Metrics
  const stats = useMemo(() => {
    const total = learningItems.length
    const mandatory = learningItems.filter((i) => i.is_mandatory)
    const mandatoryCompleted = mandatory.filter((i) => i.status === 'completed').length
    const completedTotal = learningItems.filter((i) => i.status === 'completed').length
    const inProgressTotal = learningItems.filter((i) => i.status === 'in_progress').length
    const totalMinutes = learningItems.reduce((acc, i) => acc + (i.estimated_minutes || 0), 0)

    const mandatoryCompletionRate =
      mandatory.length > 0 ? Math.round((mandatoryCompleted / mandatory.length) * 100) : 100

    return {
      total,
      mandatoryCount: mandatory.length,
      mandatoryCompleted,
      mandatoryCompletionRate,
      completedTotal,
      inProgressTotal,
      totalHours: (totalMinutes / 60).toFixed(1),
    }
  }, [learningItems])

  // Filtered List
  const filteredItems = useMemo(() => {
    return learningItems.filter((item) => {
      // Search query filter
      if (search.trim()) {
        const q = search.toLowerCase()
        const matchesTitle = item.title.toLowerCase().includes(q)
        const matchesDesc = item.description.toLowerCase().includes(q)
        const matchesTags = (item.tags || []).some((t) => t.toLowerCase().includes(q))
        if (!matchesTitle && !matchesDesc && !matchesTags) return false
      }

      // Status filter
      if (filterStatus === 'mandatory') return item.is_mandatory
      if (filterStatus === 'in_progress') return item.status === 'in_progress'
      if (filterStatus === 'completed') return item.status === 'completed'
      if (filterStatus === 'not_started') return !item.status || item.status === 'not_started'

      return true
    })
  }, [learningItems, search, filterStatus])

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)]">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
              <GraduationCap className="h-6 w-6 text-[var(--accent-indigo)]" />
              Role-Specific Learning & KT Modules
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Authoritative curriculum mapped by organizational role, tracking mandatory compliance, due dates, prerequisites, and milestone completion.
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={loadLearningData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Role Track Selector Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide border-b border-[var(--border-default)]">
          {ROLE_OPTIONS.map((tab) => {
            const isSelected = selectedRoleTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedRoleTab(tab.id)}
                className={`px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 flex-shrink-0 cursor-pointer ${
                  isSelected
                    ? 'border-indigo-500 text-[var(--accent-indigo)] bg-indigo-500/10'
                    : 'border-transparent text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-elevated)]'
                }`}
              >
                {tab.label}
                {tab.id === 'my_role' && (
                  <span className="ml-1.5 px-1.5 py-0.2 rounded text-[10px] bg-indigo-500/20 text-indigo-400">
                    Active
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Progress Strip & Compliance Metrics */}
        <div className="grid md:grid-cols-4 gap-4">
          <Card className="p-4 border-l-4 border-l-indigo-500">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Mandatory Compliance</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">{stats.mandatoryCompletionRate}%</span>
              <span className="text-xs text-[var(--text-secondary)]">
                ({stats.mandatoryCompleted}/{stats.mandatoryCount} items)
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-[var(--bg-overlay)] mt-2">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                style={{ width: `${stats.mandatoryCompletionRate}%` }}
              />
            </div>
          </Card>

          <Card className="p-4 border-l-4 border-l-emerald-500">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Completed Modules</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-400">{stats.completedTotal}</span>
              <span className="text-xs text-[var(--text-muted)]">of {stats.total} total</span>
            </div>
            <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
              Knowledge verified
            </span>
          </Card>

          <Card className="p-4 border-l-4 border-l-amber-500">
            <span className="text-xs text-[var(--text-muted)] block mb-1">In Progress</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-400">{stats.inProgressTotal}</span>
              <span className="text-xs text-[var(--text-muted)]">tracks active</span>
            </div>
            <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
              Estimated {stats.totalHours} hours total
            </span>
          </Card>

          <Card className="p-4 border-l-4 border-l-cyan-500">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Target Role Path</span>
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-bold text-cyan-300 uppercase truncate">
                {effectiveRole.replace('_', ' ')}
              </span>
            </div>
            <span className="text-[11px] text-[var(--text-muted)] mt-1 block">
              Authoritative standards
            </span>
          </Card>
        </div>

        {/* Filters and Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[var(--bg-surface)] p-3 rounded-xl border border-[var(--border-default)]">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search modules, skills, or prerequisites..."
              className="pl-9 bg-[var(--bg-base)] text-xs h-9"
            />
          </div>

          <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
            {(
              [
                { id: 'all', label: 'All Items' },
                { id: 'mandatory', label: 'Mandatory' },
                { id: 'in_progress', label: 'In Progress' },
                { id: 'completed', label: 'Completed' },
                { id: 'not_started', label: 'Not Started' },
              ] as const
            ).map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterStatus(f.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filterStatus === f.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-elevated)]'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Learning Modules Grid / Cards */}
        {loading ? (
          <div className="p-12 text-center text-sm text-[var(--text-muted)] animate-pulse">
            <RefreshCw className="h-6 w-6 animate-spin text-indigo-400 mx-auto mb-2" />
            Loading curriculum modules and completion states...
          </div>
        ) : filteredItems.length === 0 ? (
          <Card className="p-12 text-center text-sm text-[var(--text-muted)] border-dashed">
            No learning modules found matching your current filters.
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredItems.map((item) => {
              const isLocked = item.prerequisites_met === false && item.status !== 'completed'
              const isUpdating = actionInProgress === item.id

              return (
                <Card
                  key={item.id}
                  className={`transition-all duration-200 border ${
                    item.status === 'completed'
                      ? 'border-emerald-500/25 bg-emerald-950/5'
                      : item.is_mandatory
                      ? 'border-indigo-500/30 bg-[var(--bg-surface)]'
                      : 'border-[var(--border-default)] bg-[var(--bg-surface)]'
                  }`}
                >
                  <CardContent className="p-5">
                    <div className="flex flex-col lg:flex-row items-start justify-between gap-4">
                      {/* Left: Info */}
                      <div className="flex-1 space-y-2.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-base text-[var(--text-primary)]">
                            {item.title}
                          </h3>

                          {/* Mandatory vs Optional badge */}
                          {item.is_mandatory ? (
                            <Badge variant="amber" size="sm" className="font-semibold text-[10px]">
                              Mandatory for Role
                            </Badge>
                          ) : (
                            <Badge variant="default" size="sm" className="text-[10px]">
                              Recommended Elective
                            </Badge>
                          )}

                          {/* Category badge */}
                          <Badge
                            variant={categoryColors[item.category] || 'default'}
                            size="sm"
                            className="text-[10px] capitalize"
                          >
                            {item.category}
                          </Badge>

                          {/* Status Badge */}
                          {item.status === 'completed' ? (
                            <Badge variant="emerald" size="sm" className="flex items-center gap-1 text-[10px]">
                              <CheckCircle2 className="h-3 w-3" /> Completed
                            </Badge>
                          ) : item.status === 'in_progress' ? (
                            <Badge variant="indigo" size="sm" className="text-[10px]">
                              In Progress ({item.progress_pct || 0}%)
                            </Badge>
                          ) : (
                            <Badge variant="default" size="sm" className="text-[10px]">
                              Not Started
                            </Badge>
                          )}
                        </div>

                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                          {item.description}
                        </p>

                        {/* Metadata row: Estimated time, Due date, Prerequisites */}
                        <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] flex-wrap pt-1">
                          <span className="flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5 text-indigo-400" />
                            {item.estimated_minutes} mins estimated
                          </span>

                          {item.due_date && (
                            <span className="flex items-center gap-1.5 text-amber-400">
                              <Calendar className="h-3.5 w-3.5" />
                              Due: {new Date(item.due_date).toLocaleDateString()}
                            </span>
                          )}

                          {item.prerequisites && item.prerequisites.length > 0 && (
                            <span className="flex items-center gap-1.5 text-xs">
                              {item.prerequisites_met ? (
                                <span className="text-emerald-400 flex items-center gap-1">
                                  <Check className="h-3.5 w-3.5" /> Prerequisites Met
                                </span>
                              ) : (
                                <span className="text-amber-400 flex items-center gap-1">
                                  <Lock className="h-3.5 w-3.5" /> Prerequisite required: {item.prerequisites.join(', ')}
                                </span>
                              )}
                            </span>
                          )}
                        </div>

                        {/* Progress Bar */}
                        <div className="pt-2">
                          <div className="flex justify-between text-[11px] text-[var(--text-muted)] mb-1">
                            <span>Completion State</span>
                            <span className="font-mono font-medium text-indigo-400">
                              {item.progress_pct || 0}%
                            </span>
                          </div>
                          <div className="h-2 rounded-full bg-[var(--bg-overlay)] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                item.status === 'completed'
                                  ? 'bg-emerald-500'
                                  : 'bg-gradient-to-r from-indigo-500 to-violet-500'
                              }`}
                              style={{ width: `${item.progress_pct || 0}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Right: Actions */}
                      <div className="flex flex-col sm:flex-row lg:flex-col items-end gap-2 w-full lg:w-auto flex-shrink-0 pt-2 lg:pt-0">
                        {item.status === 'completed' ? (
                          <div className="text-right">
                            <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1 justify-end">
                              <CheckCircle2 className="h-4 w-4" /> Verified Complete
                            </span>
                            {item.completed_at && (
                              <span className="text-[10px] text-[var(--text-muted)] block">
                                {new Date(item.completed_at).toLocaleDateString()}
                              </span>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs text-[var(--text-muted)] mt-1"
                              onClick={() => handleUpdateProgress(item.id, 'in_progress', 50)}
                              disabled={isUpdating}
                            >
                              Revisit Module
                            </Button>
                          </div>
                        ) : item.status === 'in_progress' ? (
                          <div className="space-y-1.5 w-full sm:w-auto">
                            <div className="flex items-center gap-1.5">
                              <Button
                                variant="secondary"
                                size="sm"
                                className="text-xs"
                                onClick={() => handleUpdateProgress(item.id, 'in_progress', Math.min(100, (item.progress_pct || 0) + 25))}
                                disabled={isUpdating}
                              >
                                +25% Progress
                              </Button>
                              <Button
                                variant="primary"
                                size="sm"
                                className="text-xs bg-emerald-600 hover:bg-emerald-500"
                                onClick={() => handleUpdateProgress(item.id, 'completed', 100)}
                                disabled={isUpdating}
                              >
                                <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Mark Complete
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            className="text-xs"
                            disabled={isLocked || isUpdating}
                            onClick={() => handleUpdateProgress(item.id, 'in_progress', 15)}
                          >
                            {isLocked ? (
                              <>
                                <Lock className="h-3.5 w-3.5 mr-1" /> Locked
                              </>
                            ) : (
                              <>
                                <Play className="h-3.5 w-3.5 mr-1" /> Start Module
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
