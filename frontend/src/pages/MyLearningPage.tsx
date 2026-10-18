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
  ShieldAlert,
  Sparkles,
  UserCheck,
  FileText,
  Users,
  AlertCircle,
  Layers,
  ArrowRight,
  Send,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { learningApi, onboardingApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type {
  LearningItem,
  OnboardingJourney,
  OnboardingFormRequirement,
  OnboardingIntroduction,
  OnboardingStep,
} from '@/types'

const categoryColors: Record<string, 'indigo' | 'violet' | 'cyan' | 'emerald' | 'amber'> = {
  engineering: 'indigo',
  security: 'emerald',
  devops: 'cyan',
  process: 'violet',
  hr: 'amber',
  legal: 'violet',
  compliance: 'amber',
  payroll: 'emerald',
}

const formatRoleTitle = (role?: string) => {
  if (!role) return 'Team Member'
  return role
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function MyLearningPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'courses' | 'onboarding' | 'manager'>('courses')

  // Learning curriculum state
  const [learningItems, setLearningItems] = useState<LearningItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'mandatory' | 'role_specific' | 'in_progress' | 'completed'>('all')
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)

  // Onboarding Journey state
  const [journey, setJourney] = useState<OnboardingJourney | null>(null)
  const [journeyLoading, setJourneyLoading] = useState(false)
  const [managerRequests, setManagerRequests] = useState<any[]>([])

  // Modals & Action States
  const [selectedElectives, setSelectedElectives] = useState<string[]>([])
  const [justification, setJustification] = useState('')
  const [requestModalOpen, setRequestModalOpen] = useState(false)
  const [submittingApproval, setSubmittingApproval] = useState(false)

  // Form Submission Modal
  const [activeFormModal, setActiveFormModal] = useState<OnboardingFormRequirement | null>(null)
  const [formDataInput, setFormDataInput] = useState<Record<string, any>>({})
  const [formSigned, setFormSigned] = useState(true)
  const [submittingForm, setSubmittingForm] = useState(false)

  // Schedule Intro Modal
  const [activeIntroModal, setActiveIntroModal] = useState<OnboardingIntroduction | null>(null)
  const [schedTime, setSchedTime] = useState('')
  const [introNotes, setIntroNotes] = useState('')
  const [schedulingIntro, setSchedulingIntro] = useState(false)

  // Manager Decision Modal
  const [activeManagerReq, setActiveManagerReq] = useState<any | null>(null)
  const [managerDecisionNote, setManagerDecisionNote] = useState('')
  const [managerModifiedCourses, setManagerModifiedCourses] = useState<string[]>([])
  const [resolvingManagerReq, setResolvingManagerReq] = useState(false)

  const [notificationMsg, setNotificationMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const userRole = (user?.role || 'employee').toLowerCase()
  const isManagerOrAdmin = ['technical_lead', 'project_manager', 'admin'].includes(userRole)
  const isAssociate = !isManagerOrAdmin

  // Auto-switch away from onboarding tab if not an associate
  useEffect(() => {
    if (!isAssociate && activeTab === 'onboarding') {
      setActiveTab('courses')
    }
  }, [isAssociate, activeTab])

  // Lookup map for course approval statuses
  const courseApprovalMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const c of journey?.courses || []) {
      if (c.approval_status) {
        map.set(c.resource_id, c.approval_status)
      }
    }
    return map
  }, [journey])

  const pendingApprovalsCount = useMemo(() => {
    return (journey?.courses || []).filter((c) => c.approval_status === 'pending_approval').length
  }, [journey])

  const approvedCoursesCount = useMemo(() => {
    return (journey?.courses || []).filter((c) => c.approval_status === 'approved').length
  }, [journey])

  // Open approval modal prefilled with specific courses or all assigned courses
  const openApprovalModalForCourses = (courseIds?: string[]) => {
    if (courseIds && courseIds.length > 0) {
      setSelectedElectives(courseIds)
    } else {
      const unapprovedJourneyIds = (journey?.courses || [])
        .filter((c) => c.approval_status !== 'approved')
        .map((c) => c.resource_id)

      const unapprovedCurriculumIds = roleAndMandatoryItems
        .filter((i) => !i.is_manager_approved && !i.is_mandatory)
        .map((i) => i.id)

      const targetIds = unapprovedJourneyIds.length > 0
        ? unapprovedJourneyIds
        : unapprovedCurriculumIds.length > 0
        ? unapprovedCurriculumIds
        : roleAndMandatoryItems.map((i) => i.id)

      setSelectedElectives(targetIds)
    }
    setJustification('Submitting assigned role learning curriculum for manager review and formal sign-off.')
    setRequestModalOpen(true)
  }

  // Auto-dismiss notifications
  useEffect(() => {
    if (notificationMsg) {
      const t = setTimeout(() => setNotificationMsg(null), 5000)
      return () => clearTimeout(t)
    }
  }, [notificationMsg])

  // Load curriculum
  const loadLearningData = async () => {
    setLoading(true)
    try {
      const res = await learningApi.getLearningPaths(userRole, true)
      setLearningItems(res.items || [])
    } catch (err) {
      console.error('Failed to load role-specific learning path:', err)
      try {
        const fallback = await learningApi.listResources()
        setLearningItems(fallback.items || [])
      } catch {
        // empty fallback
      }
    } finally {
      setLoading(false)
    }
  }

  // Load journey
  const loadJourneyData = async () => {
    setJourneyLoading(true)
    try {
      const data = await onboardingApi.getJourney()
      setJourney(data)
    } catch (err) {
      console.error('Failed to load onboarding journey:', err)
    } finally {
      setJourneyLoading(false)
    }
  }

  // Load manager requests
  const loadManagerRequests = async () => {
    if (!isManagerOrAdmin) return
    try {
      const reqs = await onboardingApi.listManagerRequests()
      setManagerRequests(reqs || [])
    } catch (err) {
      console.error('Failed to load manager requests:', err)
    }
  }

  useEffect(() => {
    loadLearningData()
    loadJourneyData()
    if (isManagerOrAdmin) {
      loadManagerRequests()
    }
  }, [userRole])

  // Strict role & mandatory filter + approved manager courses
  const roleAndMandatoryItems = useMemo(() => {
    return learningItems.filter((item) => {
      const reqRoles = (item.required_for_roles || []).map((r) => String(r).toLowerCase())
      const isMandatory = Boolean(item.is_mandatory || reqRoles.includes('employee'))
      const isForMyRole = reqRoles.includes(userRole)
      const isManagerApproved = Boolean(item.is_manager_approved)
      return isMandatory || isForMyRole || isManagerApproved
    })
  }, [learningItems, userRole])

  // Combined list of courses available for manager approval
  const coursesForApproval = useMemo(() => {
    const map = new Map<string, { id: string; title: string; description: string; category?: string; estimated_minutes?: number; is_mandatory?: boolean }>()

    for (const c of journey?.courses || []) {
      if (c.approval_status !== 'approved') {
        map.set(c.resource_id, {
          id: c.resource_id,
          title: c.title,
          description: c.description || c.reason || '',
          category: c.category,
          estimated_minutes: c.estimated_minutes,
          is_mandatory: c.is_mandatory,
        })
      }
    }

    for (const item of roleAndMandatoryItems) {
      if (!item.is_manager_approved && !map.has(item.id)) {
        map.set(item.id, {
          id: item.id,
          title: item.title,
          description: item.description,
          category: item.category,
          estimated_minutes: item.estimated_minutes,
          is_mandatory: item.is_mandatory,
        })
      }
    }

    return Array.from(map.values())
  }, [journey, roleAndMandatoryItems])

  // Defensive normalization of onboarding steps to completely prevent `onboardingSteps.filter is not a function`
  const normalizedOnboardingSteps: OnboardingStep[] = useMemo(() => {
    if (!journey) return []
    const stepsCandidate = journey.onboarding_steps ?? journey.onboardingSteps
    if (Array.isArray(stepsCandidate)) {
      return stepsCandidate
    }
    return []
  }, [journey])

  // Handle module progress update
  const handleUpdateProgress = async (resourceId: string, newStatus: string, pct: number) => {
    setActionInProgress(resourceId)
    try {
      await learningApi.updateProgress(resourceId, newStatus, pct)
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
      // Refresh journey
      loadJourneyData()
    } catch (err) {
      console.error('Failed to update progress:', err)
      await loadLearningData()
    } finally {
      setActionInProgress(null)
    }
  }

  // Request Manager Approval
  const handleRequestApproval = async () => {
    if (selectedElectives.length === 0) return
    setSubmittingApproval(true)
    try {
      const res = await onboardingApi.requestApproval(
        selectedElectives,
        justification || 'Specialization electives for upcoming squad deliverables.'
      )
      if (res?.journey) {
        setJourney(res.journey)
      }
      setNotificationMsg({
        type: 'success',
        text: `Approval request for ${selectedElectives.length} course(s) submitted to your manager (${journey?.manager_name || 'Bob Harris'}) successfully!`,
      })
      setSelectedElectives([])
      setJustification('')
      setRequestModalOpen(false)
      await loadLearningData()
      await loadJourneyData()
      await loadJourneyData()
    } catch (err: any) {
      setNotificationMsg({ type: 'error', text: err.message || 'Failed to submit approval request.' })
    } finally {
      setSubmittingApproval(false)
    }
  }

  // Schedule 1:1 Intro
  const handleConfirmScheduleIntro = async () => {
    if (!activeIntroModal) return
    setSchedulingIntro(true)
    try {
      const res = await onboardingApi.scheduleIntro(
        activeIntroModal.id,
        schedTime ? new Date(schedTime).toISOString() : undefined,
        30,
        introNotes
      )
      setJourney(res.journey)
      setNotificationMsg({
        type: 'success',
        text: `Intro scheduled with ${activeIntroModal.person_name} for ${new Date(res.scheduled_at).toLocaleDateString()}!`,
      })
      setActiveIntroModal(null)
      setSchedTime('')
      setIntroNotes('')
    } catch (err: any) {
      setNotificationMsg({ type: 'error', text: err.message || 'Failed to schedule introduction.' })
    } finally {
      setSchedulingIntro(false)
    }
  }

  // Submit Form
  const handleSubmitDocumentForm = async () => {
    if (!activeFormModal) return
    setSubmittingForm(true)
    try {
      const res = await onboardingApi.submitForm(activeFormModal.id, formDataInput, formSigned)
      setJourney(res.journey)
      setNotificationMsg({ type: 'success', text: `Form '${activeFormModal.title}' submitted successfully!` })
      setActiveFormModal(null)
      setFormDataInput({})
    } catch (err: any) {
      setNotificationMsg({ type: 'error', text: err.message || 'Failed to submit form.' })
    } finally {
      setSubmittingForm(false)
    }
  }

  // Resolve Manager Approval Request
  const handleResolveManagerRequest = async (status: 'approved' | 'rejected') => {
    if (!activeManagerReq) return
    setResolvingManagerReq(true)
    try {
      const res = await onboardingApi.resolveApproval(
        activeManagerReq.id,
        status,
        managerDecisionNote,
        status === 'approved' ? managerModifiedCourses : undefined
      )
      setNotificationMsg({
        type: 'success',
        text: `Learning plan was ${res.status} successfully. Assignments updated.`,
      })
      setActiveManagerReq(null)
      setManagerDecisionNote('')
      loadManagerRequests()
      loadLearningData()
    } catch (err: any) {
      setNotificationMsg({ type: 'error', text: err.message || 'Failed to resolve approval.' })
    } finally {
      setResolvingManagerReq(false)
    }
  }

  // Summary Metrics
  const stats = useMemo(() => {
    const total = roleAndMandatoryItems.length
    const mandatory = roleAndMandatoryItems.filter(
      (i) => i.is_mandatory || (i.required_for_roles || []).map((r) => String(r).toLowerCase()).includes('employee')
    )
    const mandatoryCompleted = mandatory.filter((i) => i.status === 'completed').length
    const completedTotal = roleAndMandatoryItems.filter((i) => i.status === 'completed').length
    const inProgressTotal = roleAndMandatoryItems.filter((i) => i.status === 'in_progress').length
    const totalMinutes = roleAndMandatoryItems.reduce((acc, i) => acc + (i.estimated_minutes || 0), 0)

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
  }, [roleAndMandatoryItems])

  // Filtered List
  const filteredItems = useMemo(() => {
    return roleAndMandatoryItems.filter((item) => {
      const reqRoles = (item.required_for_roles || []).map((r) => String(r).toLowerCase())
      const isMandatory = Boolean(item.is_mandatory || reqRoles.includes('employee'))
      const isRoleSpecific = reqRoles.includes(userRole) && !reqRoles.includes('employee')

      if (search.trim()) {
        const q = search.toLowerCase()
        const matchesTitle = item.title.toLowerCase().includes(q)
        const matchesDesc = (item.description || '').toLowerCase().includes(q)
        const matchesTags = (item.tags || []).some((t) => t.toLowerCase().includes(q))
        if (!matchesTitle && !matchesDesc && !matchesTags) return false
      }

      if (filterType === 'mandatory') return isMandatory
      if (filterType === 'role_specific') return isRoleSpecific
      if (filterType === 'in_progress') return item.status === 'in_progress'
      if (filterType === 'completed') return item.status === 'completed'

      return true
    })
  }, [roleAndMandatoryItems, search, filterType, userRole])

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)]">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-7">
        {/* ─── TOAST NOTIFICATION ───────────────────────────────────────── */}
        {notificationMsg && (
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-center justify-between transition-all shadow-md ${
              notificationMsg.type === 'success'
                ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
                : 'bg-rose-950/80 border-rose-500/50 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-2">
              {notificationMsg.type === 'success' ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertCircle className="h-4 w-4 text-rose-400" />
              )}
              <span>{notificationMsg.text}</span>
            </div>
            <button onClick={() => setNotificationMsg(null)} className="opacity-70 hover:opacity-100">
              ✕
            </button>
          </div>
        )}

        {/* ─── 1. TOP HEADER & NAVIGATION TABS ─────────────────────────── */}
        <div className="p-6 rounded-3xl bg-gradient-to-r from-emerald-50/85 via-[var(--bg-surface)] to-teal-50/70 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-950 border border-emerald-200/90 dark:border-zinc-800 shadow-xs dark:shadow-none relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-emerald-400/10 via-teal-400/10 to-transparent dark:hidden rounded-full blur-3xl pointer-events-none -mr-16 -mt-16" />

          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <Badge variant="emerald" size="sm">
                  {formatRoleTitle(user?.role)} Track
                </Badge>
                {isAssociate && journey && (
                  <Badge variant="default" size="sm" className="bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-500/30">
                    Onboarding: {journey.completion_pct}% Complete
                  </Badge>
                )}
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  My Learning & Onboarding Hub
                </h1>
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-1.5 max-w-2xl">
                Personalized for <span className="font-semibold text-[var(--text-primary)]">{user?.name || 'You'}</span> ({formatRoleTitle(user?.role)}).
                Coordinated by HYPERREALM Onboard Agent.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  loadLearningData()
                  loadJourneyData()
                }}
                disabled={loading || journeyLoading}
                className="gap-2 text-xs h-9 px-3.5"
              >
                <RefreshCw className={`h-3.5 w-3.5 text-emerald-500 dark:text-emerald-400 ${loading || journeyLoading ? 'animate-spin' : ''}`} />
                Sync
              </Button>
            </div>
          </div>

          {/* Module Tabs */}
          <div className="flex items-center gap-2 mt-6 border-t border-[var(--border-default)]/60 pt-4">
            <button
              onClick={() => setActiveTab('courses')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'courses'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
              }`}
            >
              <GraduationCap className="h-4 w-4" /> My Courses & Curriculum ({roleAndMandatoryItems.length})
            </button>

            {isAssociate && (
              <button
                onClick={() => setActiveTab('onboarding')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'onboarding'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                }`}
              >
                <Sparkles className="h-4 w-4" /> Onboarding Coordinator
                {journey?.blockers && journey.blockers.length > 0 && (
                  <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                )}
              </button>
            )}

            {isManagerOrAdmin && (
              <button
                onClick={() => setActiveTab('manager')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'manager'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                }`}
              >
                <UserCheck className="h-4 w-4" /> Manager Approvals Console
                {managerRequests.filter((r) => r.is_pending).length > 0 && (
                  <Badge variant="rose" size="sm" className="ml-1 text-[10px] px-1.5 py-0.5">
                    {managerRequests.filter((r) => r.is_pending).length}
                  </Badge>
                )}
              </button>
            )}
          </div>
        </div>

        {/* ─── TAB 1: MY COURSES & CURRICULUM ─────────────────────────── */}
        {activeTab === 'courses' && (
          <div className="space-y-6">
            {/* Progress strip */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="p-4 border-l-4 border-l-emerald-500 rounded-2xl bg-[var(--bg-surface)]">
                <span className="text-xs text-[var(--text-muted)] block mb-1">Mandatory Compliance</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-[var(--text-primary)]">{stats.mandatoryCompletionRate}%</span>
                  <span className="text-xs text-[var(--text-secondary)]">
                    ({stats.mandatoryCompleted}/{stats.mandatoryCount})
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--bg-overlay)] mt-2.5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                    style={{ width: `${stats.mandatoryCompletionRate}%` }}
                  />
                </div>
              </Card>

              <Card className="p-4 border-l-4 border-l-indigo-500 rounded-2xl bg-[var(--bg-surface)]">
                <span className="text-xs text-[var(--text-muted)] block mb-1">Completed Modules</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">{stats.completedTotal}</span>
                  <span className="text-xs text-[var(--text-muted)]">of {stats.total} total</span>
                </div>
                <span className="text-[11px] text-[var(--text-secondary)] mt-1.5 block">
                  Grounded and verified
                </span>
              </Card>

              <Card className="p-4 border-l-4 border-l-amber-500 rounded-2xl bg-[var(--bg-surface)]">
                <span className="text-xs text-[var(--text-muted)] block mb-1">In Progress</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">{stats.inProgressTotal}</span>
                  <span className="text-xs text-[var(--text-muted)]">tracks active</span>
                </div>
                <span className="text-[11px] text-[var(--text-secondary)] mt-1.5 block">
                  ~{stats.totalHours} hrs estimated
                </span>
              </Card>

              <Card className="p-4 border-l-4 border-l-cyan-500 rounded-2xl bg-[var(--bg-surface)]">
                <span className="text-xs text-[var(--text-muted)] block mb-1">Learning Plan</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-sm font-bold text-cyan-700 dark:text-cyan-300">Manager Approval</span>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => openApprovalModalForCourses()}
                  className="mt-2 text-[11px] h-7 w-full border-cyan-500/30 text-cyan-700 dark:text-cyan-300 hover:bg-cyan-600/20"
                >
                  Request Manager Approval
                </Button>
              </Card>
            </div>

            {/* Associate Manager Approval Action Banner */}
            {isAssociate && (
              <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-50/85 via-emerald-50/60 to-[var(--bg-surface)] dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-950 border border-cyan-200 dark:border-zinc-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs dark:shadow-none">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-300 dark:border-cyan-500/30 text-cyan-600 dark:text-cyan-400 mt-0.5">
                    <UserCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">Manager Approval for Assigned Courses</h4>
                      {pendingApprovalsCount > 0 && (
                        <Badge variant="amber" size="sm" className="text-[10px]">
                          {pendingApprovalsCount} Pending Review
                        </Badge>
                      )}
                      {approvedCoursesCount > 0 && (
                        <Badge variant="emerald" size="sm" className="text-[10px]">
                          {approvedCoursesCount} Approved
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      After reviewing your assigned role courses below, request approval from <span className="font-semibold text-[var(--text-primary)]">{journey?.manager_name || 'Bob Harris'}</span> for formal onboarding sign-off.
                    </p>
                  </div>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => openApprovalModalForCourses()}
                  disabled={submittingApproval}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-9 px-4 flex-shrink-0 gap-1.5 shadow-sm"
                >
                  <Send className="h-3.5 w-3.5" /> Request Manager for Approval
                </Button>
              </div>
            )}

            {/* Filters */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[var(--bg-surface)] p-3 rounded-2xl border border-[var(--border-default)]">
              <div className="relative w-full sm:w-80">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search my role modules, skills, or tags..."
                  className="pl-9 bg-[var(--bg-base)] text-xs h-9 rounded-xl text-[var(--text-primary)]"
                />
              </div>

              <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
                <button
                  onClick={() => setFilterType('all')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterType === 'all'
                      ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/40 shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  All Assigned ({roleAndMandatoryItems.length})
                </button>
                <button
                  onClick={() => setFilterType('mandatory')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterType === 'mandatory'
                      ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/40 shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  Mandatory Only
                </button>
                <button
                  onClick={() => setFilterType('role_specific')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterType === 'role_specific'
                      ? 'bg-indigo-500/15 text-indigo-800 dark:text-indigo-300 border border-indigo-500/40 shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  Role Specialization
                </button>
                <button
                  onClick={() => setFilterType('in_progress')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterType === 'in_progress'
                      ? 'bg-cyan-500/15 text-cyan-800 dark:text-cyan-300 border border-cyan-500/40 shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  In Progress
                </button>
                <button
                  onClick={() => setFilterType('completed')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterType === 'completed'
                      ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/40 shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  Completed
                </button>
              </div>
            </div>

            {/* Courses List */}
            {loading ? (
              <div className="p-12 text-center text-sm text-[var(--text-muted)] animate-pulse">
                <RefreshCw className="h-6 w-6 animate-spin text-emerald-400 mx-auto mb-2" />
                Loading role curriculum modules and completion states...
              </div>
            ) : filteredItems.length === 0 ? (
              <Card className="p-12 text-center text-sm text-[var(--text-muted)] border-dashed">
                <GraduationCap className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">No modules found</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto">
                  No learning tracks match the current filter for your role.
                </p>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredItems.map((item) => {
                  const reqRoles = (item.required_for_roles || []).map((r) => String(r).toLowerCase())
                  const isMandatory = Boolean(item.is_mandatory || reqRoles.includes('employee'))
                  const isLocked = item.prerequisites_met === false && item.status !== 'completed'
                  const isUpdating = actionInProgress === item.id
                  const isManagerApproved = Boolean(item.is_manager_approved)

                  return (
                    <Card
                      key={item.id}
                      className={`transition-all duration-200 border rounded-2xl ${
                        item.status === 'completed'
                          ? 'border-emerald-500/30 bg-emerald-950/10'
                          : isMandatory
                          ? 'border-amber-500/30 bg-[var(--bg-surface)]'
                          : 'border-[var(--border-default)] bg-[var(--bg-surface)]'
                      }`}
                    >
                      <CardContent className="p-5">
                        <div className="flex flex-col lg:flex-row items-start justify-between gap-4">
                          <div className="flex-1 space-y-2.5">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-bold text-base text-[var(--text-primary)]">{item.title}</h3>

                              {isMandatory ? (
                                <Badge variant="rose" size="sm" className="font-semibold text-[10px] gap-1">
                                  <ShieldAlert className="h-2.5 w-2.5" /> Mandatory Compliance
                                </Badge>
                              ) : courseApprovalMap.get(item.id) === 'approved' || isManagerApproved ? (
                                <Badge variant="cyan" size="sm" className="font-semibold text-[10px] gap-1">
                                  <Check className="h-2.5 w-2.5" /> Manager Approved
                                </Badge>
                              ) : courseApprovalMap.get(item.id) === 'pending_approval' ? (
                                <Badge variant="amber" size="sm" className="font-semibold text-[10px] gap-1">
                                  <Clock className="h-2.5 w-2.5" /> Pending Review
                                </Badge>
                              ) : (
                                <Badge variant="violet" size="sm" className="text-[10px] gap-1">
                                  <Sparkles className="h-2.5 w-2.5" /> Role Specialization
                                </Badge>
                              )}

                              <Badge
                                variant={categoryColors[item.category] || 'indigo'}
                                size="sm"
                                className="text-[10px] capitalize"
                              >
                                {item.category}
                              </Badge>

                              {item.status === 'completed' ? (
                                <Badge variant="emerald" size="sm" className="flex items-center gap-1 text-[10px]">
                                  <CheckCircle2 className="h-3 w-3" /> Completed
                                </Badge>
                              ) : item.status === 'in_progress' ? (
                                <Badge variant="cyan" size="sm" className="text-[10px]">
                                  In Progress ({item.progress_pct || 0}%)
                                </Badge>
                              ) : (
                                <Badge variant="default" size="sm" className="text-[10px]">
                                  Not Started
                                </Badge>
                              )}
                            </div>

                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{item.description}</p>

                            <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] flex-wrap pt-1 font-mono">
                              <span className="flex items-center gap-1.5">
                                <Clock className="h-3.5 w-3.5 text-emerald-400" />
                                {item.estimated_minutes} mins estimated
                              </span>

                              {item.due_date && (
                                <span className="flex items-center gap-1.5 text-amber-400 font-semibold">
                                  <Calendar className="h-3.5 w-3.5" />
                                  Due: {new Date(item.due_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>

                            <div className="pt-2">
                              <div className="flex justify-between text-[11px] text-[var(--text-muted)] mb-1">
                                <span>Module Completion</span>
                                <span className="font-mono font-medium text-emerald-400">{item.progress_pct || 0}%</span>
                              </div>
                              <div className="h-2 rounded-full bg-[var(--bg-overlay)] overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    item.status === 'completed'
                                      ? 'bg-emerald-500'
                                      : 'bg-gradient-to-r from-emerald-500 to-teal-400'
                                  }`}
                                  style={{ width: `${item.progress_pct || 0}%` }}
                                />
                              </div>
                            </div>
                          </div>

                          <div className="flex flex-col sm:flex-row lg:flex-col items-end gap-2 w-full lg:w-auto flex-shrink-0 pt-2 lg:pt-0">
                            {item.status === 'completed' ? (
                              <div className="text-right">
                                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1 justify-end">
                                  <CheckCircle2 className="h-4 w-4" /> Verified Complete
                                </span>
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
                                    className="text-xs h-8"
                                    onClick={() =>
                                      handleUpdateProgress(item.id, 'in_progress', Math.min(100, (item.progress_pct || 0) + 25))
                                    }
                                    disabled={isUpdating}
                                  >
                                    +25% Progress
                                  </Button>
                                  <Button
                                    variant="primary"
                                    size="sm"
                                    className="text-xs h-8 bg-emerald-600 hover:bg-emerald-500"
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
                                className="text-xs h-8 px-4"
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

                            {isAssociate && !isMandatory && courseApprovalMap.get(item.id) !== 'approved' && !item.is_manager_approved && (
                              <div className="mt-1">
                                {courseApprovalMap.get(item.id) === 'pending_approval' ? (
                                  <span className="text-[11px] text-amber-400 font-medium flex items-center gap-1 justify-end">
                                    <Clock className="h-3 w-3" /> Awaiting Review
                                  </span>
                                ) : (
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    className="text-xs h-7 px-2.5 text-cyan-300 border-cyan-500/30 hover:bg-cyan-600/20"
                                    onClick={() => openApprovalModalForCourses([item.id])}
                                  >
                                    <Send className="h-3 w-3 mr-1" /> Request Approval
                                  </Button>
                                )}
                              </div>
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
        )}

        {/* ─── TAB 2: ONBOARDING COORDINATOR ──────────────────────────── */}
        {activeTab === 'onboarding' && isAssociate && (
          <div className="space-y-7">
            {journeyLoading ? (
              <div className="p-12 text-center text-sm text-[var(--text-muted)]">
                <RefreshCw className="h-6 w-6 animate-spin text-emerald-400 mx-auto mb-2" />
                Loading personalized onboarding journey...
              </div>
            ) : journey ? (
              <>
                {/* 1. Journey Overview Card */}
                <div className="p-6 rounded-3xl bg-[var(--bg-surface)] border border-emerald-500/30 relative overflow-hidden">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="emerald" size="sm">
                          Active Onboarding
                        </Badge>
                        <span className="text-xs text-[var(--text-muted)]">
                          Started: {new Date(journey.start_date).toLocaleDateString()}
                        </span>
                      </div>
                      <h2 className="text-xl font-bold text-[var(--text-primary)]">Associate Onboarding Progress</h2>
                      <p className="text-xs text-[var(--text-secondary)]">
                        Manager: <span className="text-[var(--text-primary)] font-medium">{journey.manager_name || 'Bob Harris'}</span> • Buddy:{' '}
                        <span className="text-[var(--text-primary)] font-medium">{journey.buddy_name || 'Carol Adams'}</span>
                      </p>
                      {journey.next_action && (
                        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                          <ArrowRight className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                          <span>
                            <strong>Next Priority:</strong> {journey.next_action}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-6 flex-shrink-0">
                      <div className="text-center">
                        <span className="text-3xl font-extrabold font-mono text-emerald-500 dark:text-emerald-400">{journey.completion_pct}%</span>
                        <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Total Completion</span>
                      </div>
                      <div className="space-y-1.5 text-xs text-[var(--text-secondary)] border-l border-[var(--border-default)] pl-4">
                        <div>Learning: <strong className="text-[var(--text-primary)]">{journey.learning_completion_pct}%</strong></div>
                        <div>Documents: <strong className="text-[var(--text-primary)]">{journey.forms_completion_pct}%</strong></div>
                        <div>People & 1:1s: <strong className="text-[var(--text-primary)]">{journey.intros_completion_pct}%</strong></div>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="h-2 rounded-full bg-[var(--bg-overlay)] mt-5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 transition-all duration-500"
                      style={{ width: `${journey.completion_pct}%` }}
                    />
                  </div>
                </div>

                {/* 2. Assigned Role Courses & Manager Approval */}
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                        <GraduationCap className="h-4 w-4 text-emerald-400" /> Assigned Role Courses & Curriculum ({journey.courses.length})
                      </h3>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                        Assigned specifically for your role. Review modules and request manager approval for formal onboarding sign-off.
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => openApprovalModalForCourses()}
                      disabled={submittingApproval}
                      className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs h-8 px-3.5 flex-shrink-0 gap-1.5 shadow-sm"
                    >
                      <Send className="h-3.5 w-3.5" /> Request Manager for Approval
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {journey.courses.map((course) => {
                      const isPending = course.approval_status === 'pending_approval'
                      const isApproved = course.approval_status === 'approved'
                      const isRejected = course.approval_status === 'rejected'

                      return (
                        <Card
                          key={course.resource_id}
                          className="p-4 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] flex flex-col justify-between"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center justify-between flex-wrap gap-1.5">
                              <Badge variant={course.is_mandatory ? 'rose' : 'violet'} size="sm" className="text-[10px]">
                                {course.is_mandatory ? 'Mandatory Compliance' : 'Role Specialization'}
                              </Badge>

                              {isApproved ? (
                                <Badge variant="emerald" size="sm" className="text-[10px] gap-1">
                                  <Check className="h-3 w-3" /> Manager Approved
                                </Badge>
                              ) : isPending ? (
                                <Badge variant="amber" size="sm" className="text-[10px] gap-1">
                                  <Clock className="h-3 w-3" /> Pending Review
                                </Badge>
                              ) : isRejected ? (
                                <Badge variant="rose" size="sm" className="text-[10px]">
                                  Revision Needed
                                </Badge>
                              ) : (
                                <Badge variant="default" size="sm" className="text-[10px]">
                                  Unsubmitted
                                </Badge>
                              )}
                            </div>

                            <h4 className="font-bold text-sm text-[var(--text-primary)]">{course.title}</h4>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2">
                              {course.description || course.reason || 'Curriculum module assigned for your specialization track.'}
                            </p>

                            <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)] font-mono pt-1">
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3 text-emerald-400" />
                                {course.estimated_minutes} mins
                              </span>
                              <span className="capitalize">{course.category}</span>
                            </div>
                          </div>

                          <div className="mt-4 pt-3 border-t border-[var(--border-default)] flex items-center justify-between gap-2">
                            <div className="text-[11px] text-[var(--text-muted)]">
                              {course.progress_pct > 0 ? (
                                <span className="text-emerald-500 dark:text-emerald-400 font-mono font-medium">{course.progress_pct}% completed</span>
                              ) : (
                                <span>Status: {course.status}</span>
                              )}
                            </div>

                            {!isApproved && !isPending && (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => openApprovalModalForCourses([course.resource_id])}
                                className="text-xs h-7 px-2.5 text-cyan-700 dark:text-cyan-300 border-cyan-500/30 hover:bg-cyan-600/20"
                              >
                                <Send className="h-3 w-3 mr-1" /> Request Approval
                              </Button>
                            )}

                            {isPending && (
                              <span className="text-[11px] text-amber-500 dark:text-amber-400 font-medium flex items-center gap-1">
                                <Clock className="h-3 w-3" /> Awaiting Manager Sign-off
                              </span>
                            )}

                            {isApproved && (
                              <span className="text-[11px] text-emerald-500 dark:text-emerald-400 font-medium flex items-center gap-1">
                                <Check className="h-3 w-3" /> Enrolled in Curriculum
                              </span>
                            )}
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>

                {/* 3. Onboarding Timeline Milestones (Defensively normalized steps) */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                    <Layers className="h-4 w-4 text-emerald-400" /> Structured 30-Day Onboarding Milestones
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {normalizedOnboardingSteps.map((step) => {
                      const isComplete = step.status === 'completed'
                      const isCurrent = step.status === 'in_progress'

                      return (
                        <Card
                          key={step.id}
                          className={`p-4 rounded-2xl border transition-all ${
                            isComplete
                              ? 'border-emerald-500/30 bg-emerald-500/5'
                              : isCurrent
                              ? 'border-emerald-500/50 bg-[var(--bg-surface)] shadow-sm'
                              : 'border-[var(--border-default)] bg-[var(--bg-surface)] opacity-85'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant={isComplete ? 'emerald' : isCurrent ? 'cyan' : 'default'} size="sm">
                              {step.phase}
                            </Badge>
                            <span className="text-[10px] text-[var(--text-muted)] font-mono">Day {step.due_days}</span>
                          </div>
                          <h4 className="font-bold text-sm text-[var(--text-primary)] mb-2">{step.title}</h4>
                          <ul className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                            {(step.items || []).map((itm, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="text-emerald-500 dark:text-emerald-400 mt-0.5">•</span>
                                <span>{itm}</span>
                              </li>
                            ))}
                          </ul>
                        </Card>
                      )
                    })}
                  </div>
                </div>

                {/* 3. Required Forms & Documents */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                      <FileText className="h-4 w-4 text-emerald-400" /> Compliance Forms & Document Requirements ({journey.forms.length})
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {journey.forms.map((form) => {
                      const isSubmitted = form.status === 'submitted' || form.status === 'verified'

                      return (
                        <Card key={form.id} className="p-4 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] flex flex-col justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Badge variant={isSubmitted ? 'emerald' : 'amber'} size="sm">
                                {isSubmitted ? 'Submitted' : 'Pending Submission'}
                              </Badge>
                              {form.is_sensitive && (
                                <Badge variant="rose" size="sm" className="text-[9px]">
                                  Confidential
                                </Badge>
                              )}
                            </div>
                            <h4 className="font-bold text-sm text-[var(--text-primary)]">{form.title}</h4>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{form.description}</p>
                          </div>

                          <div className="mt-4 pt-3 border-t border-[var(--border-default)] flex items-center justify-between">
                            <span className="text-[11px] text-[var(--text-muted)]">
                              {form.due_date ? `Due: ${new Date(form.due_date).toLocaleDateString()}` : 'Due Soon'}
                            </span>
                            {isSubmitted ? (
                              <span className="text-xs text-emerald-500 dark:text-emerald-400 flex items-center gap-1 font-semibold">
                                <CheckCircle2 className="h-3.5 w-3.5" /> Filed
                              </span>
                            ) : (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  setActiveFormModal(form)
                                  setFormDataInput(form.prepopulated_fields || {})
                                }}
                                className="text-xs h-7 px-3 bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30 hover:bg-emerald-600 hover:text-white"
                              >
                                Complete Form
                              </Button>
                            )}
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>

                {/* 4. People & Introductions */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                      <Users className="h-4 w-4 text-emerald-400" /> People & Team Introductions ({journey.introductions.length})
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {journey.introductions.map((intro) => {
                      const isScheduled = intro.status === 'scheduled' || intro.status === 'completed'

                      return (
                        <Card key={intro.id} className="p-4 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] flex flex-col justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Badge variant="cyan" size="sm">
                                {intro.relationship}
                              </Badge>
                              <Badge variant={isScheduled ? 'emerald' : 'default'} size="sm">
                                {intro.status}
                              </Badge>
                            </div>
                            <div>
                              <h4 className="font-bold text-sm text-[var(--text-primary)]">{intro.person_name}</h4>
                              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">{intro.role}</span>
                            </div>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{intro.meeting_purpose}</p>
                          </div>

                          <div className="mt-4 pt-3 border-t border-[var(--border-default)] flex items-center justify-between">
                            <span className="text-[11px] text-[var(--text-muted)] truncate max-w-[140px]">{intro.email}</span>
                            {isScheduled ? (
                              <span className="text-xs text-emerald-500 dark:text-emerald-400 font-semibold flex items-center gap-1">
                                <CheckCircle2 className="h-3.5 w-3.5" /> 1:1 Set
                              </span>
                            ) : (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  setActiveIntroModal(intro)
                                  setIntroNotes(`Intro meeting: ${intro.meeting_purpose}`)
                                }}
                                className="text-xs h-7 px-3 bg-cyan-500/15 text-cyan-800 dark:text-cyan-300 border-cyan-500/30 hover:bg-cyan-600 hover:text-white"
                              >
                                Schedule 1:1
                              </Button>
                            )}
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>
              </>
            ) : (
              <Card className="p-12 text-center text-sm text-[var(--text-muted)] border-dashed">
                <Sparkles className="h-8 w-8 text-emerald-400 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Generate Your Personalized Onboarding Plan</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto mb-4">
                  Construct your tailored role curriculum, 1:1 connections, and required compliance agreements.
                </p>
                <Button variant="primary" onClick={loadJourneyData} className="text-xs">
                  Generate Plan Now
                </Button>
              </Card>
            )}
          </div>
        )}

        {/* ─── TAB 3: MANAGER REVIEW CONSOLE ──────────────────────────── */}
        {activeTab === 'manager' && isManagerOrAdmin && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[var(--text-primary)]">Associate Course Approvals Console</h2>
                <p className="text-xs text-[var(--text-secondary)]">
                  Review, modify, and authorize recommended course tracks for your direct reports.
                </p>
              </div>
              <Button variant="secondary" size="sm" onClick={loadManagerRequests} className="text-xs">
                Refresh Queue
              </Button>
            </div>

            {managerRequests.length === 0 ? (
              <Card className="p-12 text-center text-sm text-[var(--text-muted)] border-dashed">
                <UserCheck className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">No Approval Requests Pending</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  All learning plans submitted by your associates have been reviewed and approved.
                </p>
              </Card>
            ) : (
              <div className="space-y-4">
                {managerRequests.map((req) => {
                  const payload = req.action_payload || {}
                  const courses: any[] = payload.courses || []
                  const isPending = req.status === 'pending'

                  return (
                    <Card
                      key={req.id}
                      className={`p-5 rounded-2xl border transition-all ${
                        isPending ? 'border-amber-500/40 bg-[var(--bg-surface)]' : 'border-[var(--border-default)] bg-[var(--bg-surface)] opacity-75'
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant={isPending ? 'amber' : req.status === 'approved' ? 'emerald' : 'rose'} size="sm">
                              {req.status.toUpperCase()}
                            </Badge>
                            <span className="text-xs text-[var(--text-muted)]">
                              Submitted: {new Date(req.requested_at).toLocaleDateString()}
                            </span>
                          </div>
                          <h3 className="font-bold text-base text-[var(--text-primary)]">{req.title}</h3>
                          <p className="text-xs text-[var(--text-secondary)]">{req.description}</p>

                          {/* Proposed courses preview */}
                          <div className="pt-2">
                            <span className="text-xs text-[var(--text-primary)] font-semibold block mb-1.5">Proposed Courses ({courses.length}):</span>
                            <div className="flex flex-wrap gap-2">
                              {courses.map((c) => (
                                <Badge key={c.id} variant="default" size="sm" className="text-xs">
                                  {c.title} ({c.estimated_minutes} min)
                                </Badge>
                              ))}
                            </div>
                          </div>

                          {req.decision_note && (
                            <div className="mt-2 text-xs text-amber-800 dark:text-amber-300 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
                              <strong>Decision Note:</strong> {req.decision_note}
                            </div>
                          )}
                        </div>

                        {isPending && (
                          <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0 pt-2 md:pt-0">
                            <Button
                              variant="primary"
                              size="sm"
                              className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
                              onClick={() => {
                                setActiveManagerReq(req)
                                setManagerModifiedCourses(payload.course_ids || [])
                              }}
                            >
                              Review & Decide
                            </Button>
                          </div>
                        )}
                      </div>
                    </Card>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ─── MODAL: REQUEST MANAGER APPROVAL ─────────────────────────── */}
        {requestModalOpen && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[var(--bg-surface)] border border-cyan-500/30 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <UserCheck className="h-4 w-4 text-cyan-500 dark:text-cyan-400" /> Request Manager Approval for Learning Plan
                </h3>
                <button onClick={() => setRequestModalOpen(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                  ✕
                </button>
              </div>

              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Review and submit your assigned role curriculum modules to your manager (<span className="text-[var(--text-primary)] font-medium">{journey?.manager_name || 'Bob Harris'}</span>) for formal onboarding sign-off.
              </p>

              {/* Selection Summary and Toggle */}
              <div className="flex items-center justify-between py-1 border-b border-[var(--border-default)]/60">
                <span className="text-xs text-[var(--text-muted)] font-mono">
                  {selectedElectives.length} module{selectedElectives.length === 1 ? '' : 's'} selected
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedElectives(coursesForApproval.map((c) => c.id))}
                    className="text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline font-medium"
                  >
                    Select All
                  </button>
                  <span className="text-[var(--text-muted)]">•</span>
                  <button
                    type="button"
                    onClick={() => setSelectedElectives([])}
                    className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  >
                    Clear All
                  </button>
                </div>
              </div>

              {/* Course Selection */}
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {coursesForApproval.map((c) => {
                  const isChecked = selectedElectives.includes(c.id)
                  return (
                    <label
                      key={c.id}
                      className={`flex items-start gap-2.5 p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                        isChecked
                          ? 'border-cyan-500/50 bg-cyan-500/10 text-[var(--text-primary)]'
                          : 'border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-secondary)]'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedElectives([...selectedElectives, c.id])
                          } else {
                            setSelectedElectives(selectedElectives.filter((id) => id !== c.id))
                          }
                        }}
                        className="mt-0.5 rounded text-cyan-500 focus:ring-cyan-500"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <strong className="text-[var(--text-primary)] block">{c.title}</strong>
                          {c.is_mandatory && (
                            <Badge variant="rose" size="sm" className="text-[9px]">
                              Mandatory
                            </Badge>
                          )}
                        </div>
                        <span className="text-[11px] text-[var(--text-muted)] line-clamp-2">{c.description}</span>
                        {c.estimated_minutes && (
                          <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono block mt-1">
                            ~{c.estimated_minutes} mins • {c.category || 'Specialization'}
                          </span>
                        )}
                      </div>
                    </label>
                  )
                })}
              </div>

              {/* Justification input */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-[var(--text-primary)]">Business Justification & Note for Manager</label>
                <textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder="Explain your goals or note any focus areas for your manager..."
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-xl p-2.5 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-cyan-500 min-h-[70px]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-default)]">
                <Button variant="ghost" size="sm" onClick={() => setRequestModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleRequestApproval}
                  disabled={selectedElectives.length === 0 || submittingApproval}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white"
                >
                  {submittingApproval ? 'Submitting Request...' : `Submit ${selectedElectives.length} Course(s) for Approval`}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── MODAL: COMPLETE COMPLIANCE FORM ─────────────────────────── */}
        {activeFormModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[var(--bg-surface)] border border-emerald-500/30 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <FileText className="h-4 w-4 text-emerald-500 dark:text-emerald-400" /> {activeFormModal.title}
                </h3>
                <button onClick={() => setActiveFormModal(null)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                  ✕
                </button>
              </div>

              <p className="text-xs text-[var(--text-secondary)]">{activeFormModal.description}</p>

              {/* Form Fields tailored to Form ID */}
              <div className="space-y-3">
                {activeFormModal.id === 'form_i9_identity' && (
                  <>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Document Type *</label>
                      <Input
                        value={formDataInput.document_type || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, document_type: e.target.value })}
                        placeholder="e.g. US Passport, Permanent Resident Card, Driver's License"
                        className="bg-[var(--bg-base)] text-xs h-9 text-[var(--text-primary)]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Document Number *</label>
                      <Input
                        value={formDataInput.document_number || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, document_number: e.target.value })}
                        placeholder="Enter identification document number"
                        className="bg-[var(--bg-base)] text-xs h-9 text-[var(--text-primary)]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Issuing Authority</label>
                      <Input
                        value={formDataInput.issuing_authority || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, issuing_authority: e.target.value })}
                        placeholder="e.g. US Department of State, State DMV"
                        className="bg-[var(--bg-base)] text-xs h-9 text-[var(--text-primary)]"
                      />
                    </div>
                  </>
                )}

                {activeFormModal.id === 'form_direct_deposit' && (
                  <>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Bank Name *</label>
                      <Input
                        value={formDataInput.bank_name || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, bank_name: e.target.value })}
                        placeholder="e.g. Chase, Bank of America, Wells Fargo"
                        className="bg-[var(--bg-base)] text-xs h-9 text-[var(--text-primary)]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Routing Number (9 digits) *</label>
                      <Input
                        value={formDataInput.routing_number || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, routing_number: e.target.value })}
                        placeholder="021000021"
                        className="bg-[var(--bg-base)] text-xs h-9 font-mono text-[var(--text-primary)]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-[var(--text-primary)]">Account Number *</label>
                      <Input
                        type="password"
                        value={formDataInput.account_number || ''}
                        onChange={(e) => setFormDataInput({ ...formDataInput, account_number: e.target.value })}
                        placeholder="Enter checking/savings account number"
                        className="bg-[var(--bg-base)] text-xs h-9 font-mono text-[var(--text-primary)]"
                      />
                    </div>
                  </>
                )}

                {(activeFormModal.id === 'form_code_of_conduct' ||
                  activeFormModal.id === 'form_nda_ip' ||
                  activeFormModal.id === 'form_security_compliance') && (
                  <div className="space-y-2.5">
                    <div className="p-3 bg-[var(--bg-base)] rounded-xl border border-[var(--border-default)] text-xs text-[var(--text-secondary)] space-y-1">
                      <p>
                        By signing, you certify under penalty of perjury that you have read and agree to all standards in the{' '}
                        <strong className="text-[var(--text-primary)]">{activeFormModal.title}</strong>.
                      </p>
                      <p className="text-[11px] text-[var(--text-muted)]">
                        Verified Associate: {user?.name} ({user?.email})
                      </p>
                    </div>
                    <label className="flex items-center gap-2 text-xs text-[var(--text-primary)] cursor-pointer pt-1">
                      <input
                        type="checkbox"
                        checked={formSigned}
                        onChange={(e) => setFormSigned(e.target.checked)}
                        className="rounded text-emerald-500 focus:ring-emerald-500"
                      />
                      <span>I agree and confirm digital execution of this agreement.</span>
                    </label>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-default)]">
                <Button variant="ghost" size="sm" onClick={() => setActiveFormModal(null)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSubmitDocumentForm}
                  disabled={submittingForm || !formSigned}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  {submittingForm ? 'Submitting...' : 'Submit Form for Verification'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── MODAL: SCHEDULE 1:1 INTRO ───────────────────────────────── */}
        {activeIntroModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[var(--bg-surface)] border border-emerald-500/30 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-cyan-500 dark:text-cyan-400" /> Schedule Onboarding 1:1
                </h3>
                <button onClick={() => setActiveIntroModal(null)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                  ✕
                </button>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-[var(--text-muted)]">Meeting With</span>
                <p className="text-sm font-bold text-[var(--text-primary)]">
                  {activeIntroModal.person_name} ({activeIntroModal.relationship})
                </p>
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium block">{activeIntroModal.role}</span>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-[var(--text-primary)]">Select Date & Time</label>
                <Input
                  type="datetime-local"
                  value={schedTime}
                  onChange={(e) => setSchedTime(e.target.value)}
                  className="bg-[var(--bg-base)] text-xs h-9 text-[var(--text-primary)]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-[var(--text-primary)]">Agenda & Notes</label>
                <textarea
                  value={introNotes}
                  onChange={(e) => setIntroNotes(e.target.value)}
                  placeholder="Notes or agenda for the 1:1..."
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-xl p-2.5 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-cyan-500 min-h-[60px]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-default)]">
                <Button variant="ghost" size="sm" onClick={() => setActiveIntroModal(null)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleConfirmScheduleIntro}
                  disabled={schedulingIntro}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white"
                >
                  {schedulingIntro ? 'Scheduling...' : 'Send Calendar Invite'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── MODAL: MANAGER DECISION & MODIFICATION ─────────────────── */}
        {activeManagerReq && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[var(--bg-surface)] border border-emerald-500/30 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <UserCheck className="h-4 w-4 text-emerald-500 dark:text-emerald-400" /> Review Learning Plan Request
                </h3>
                <button onClick={() => setActiveManagerReq(null)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                  ✕
                </button>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-[var(--text-muted)]">Request</span>
                <p className="text-sm font-bold text-[var(--text-primary)]">{activeManagerReq.title}</p>
                <p className="text-xs text-[var(--text-secondary)]">{activeManagerReq.description}</p>
              </div>

              {/* Course Modification Checkboxes */}
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-[var(--text-primary)]">Select Courses to Approve:</span>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {(activeManagerReq.action_payload?.courses || []).map((c: any) => {
                    const isChecked = managerModifiedCourses.includes(c.id)
                    return (
                      <label
                        key={c.id}
                        className={`flex items-start gap-2 p-2.5 rounded-xl border text-xs cursor-pointer ${
                          isChecked
                            ? 'border-emerald-500/50 bg-emerald-500/10 text-[var(--text-primary)]'
                            : 'border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-muted)]'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setManagerModifiedCourses([...managerModifiedCourses, c.id])
                            } else {
                              setManagerModifiedCourses(managerModifiedCourses.filter((id) => id !== c.id))
                            }
                          }}
                          className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-500"
                        />
                        <div>
                          <strong>{c.title}</strong> ({c.estimated_minutes} min)
                        </div>
                      </label>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-[var(--text-primary)]">Manager Comments</label>
                <textarea
                  value={managerDecisionNote}
                  onChange={(e) => setManagerDecisionNote(e.target.value)}
                  placeholder="Record comments or guidance for the associate..."
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-xl p-2.5 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-emerald-500 min-h-[60px]"
                />
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[var(--border-default)]">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleResolveManagerRequest('rejected')}
                  disabled={resolvingManagerReq}
                  className="text-xs text-rose-600 dark:text-rose-300 border-rose-500/30 hover:bg-rose-500/10"
                >
                  Reject Request
                </Button>

                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setActiveManagerReq(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleResolveManagerRequest('approved')}
                    disabled={resolvingManagerReq || managerModifiedCourses.length === 0}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs"
                  >
                    {resolvingManagerReq ? 'Assigning...' : `Approve & Assign (${managerModifiedCourses.length})`}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
