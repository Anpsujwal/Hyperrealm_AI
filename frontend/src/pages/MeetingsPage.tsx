import { useState, useEffect, useMemo, useRef } from 'react'
import {
  CalendarDays,
  Clock,
  Video,
  Users,
  Plus,
  RefreshCw,
  X,
  FileText,
  Calendar as CalendarIcon,
  Download,
  Mic,
  MicOff,
  VideoOff,
  Sparkles,
  CheckCircle2,
  Copy,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Check,
  Crown,
  ArrowRight,
  CalendarCheck,
  AlertCircle,
  Bell,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { meetingsApi, usersApi, notificationsApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { MeetingItem, CalendarAvailabilityResult, User, NotificationItem } from '@/types'

// Mock transcript seed for meetings that do not have recorded notes yet
const DEFAULT_TRANSCRIPTS: Record<string, { transcript: string; summary: string; actionItems: string[] }> = {
  default: {
    transcript: `[00:01] Carol Wu: Good morning everyone, let's review today's technical sync and service latency findings.
[00:14] Priya Sharma: I noticed the Redis token caching TTL was set to 15 minutes, causing recurrent auth renewal spikes.
[00:32] Bob Smith: We should align it with the 45-minute standard specified in our Engineering Security Guidelines v3.0.
[00:51] Carol Wu: Agreed. I will assign the cache TTL alignment task to our backend developer, and we will audit the metrics before Friday.
[01:10] Priya Sharma: Sounds great. I have already drafted the zero-trust acceptance criteria.`,
    summary: 'Reviewed Redis authentication cache TTL latency spikes. The team aligned on updating token expiration to 45 minutes in compliance with Engineering Security Guidelines v3.0.',
    actionItems: [
      'Update Redis session cache token expiration from 15m to 45m',
      'Verify zero-trust authentication compliance in staging before deployment',
      'Publish post-sync latency metric graphs to engineering dashboard',
    ],
  },
}

export function MeetingsPage() {
  const { user } = useAuth()
  const [meetings, setMeetings] = useState<MeetingItem[]>([])
  const [directoryUsers, setDirectoryUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'schedule' | 'calendar'>('schedule')
  const [filterType, setFilterType] = useState<'all' | 'pending_rsvp' | 'upcoming' | 'today' | 'with_notes'>('all')

  // Toast / feedback notification
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)

  // Modals & Active Call
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [selectedMeetingNotes, setSelectedMeetingNotes] = useState<MeetingItem | null>(null)
  const [activeCallMeeting, setActiveCallMeeting] = useState<MeetingItem | null>(null)
  const [calendarSyncing, setCalendarSyncing] = useState(false)
  const [calendarSyncedAt, setCalendarSyncedAt] = useState<string>('Just now')

  // Notifications Popover
  const [showNotificationsModal, setShowNotificationsModal] = useState(false)
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [loadingNotifs, setLoadingNotifs] = useState(false)

  // Meeting Form
  const [title, setTitle] = useState('')
  const [type, setType] = useState('general')
  const [scheduledAt, setScheduledAt] = useState('')
  const [duration, setDuration] = useState('45')
  const [agendaText, setAgendaText] = useState('')
  const [selectedAttendeeIds, setSelectedAttendeeIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  // Collision Checking state for Schedule Form
  const [checkingCollision, setCheckingCollision] = useState(false)
  const [collisionResult, setCollisionResult] = useState<CalendarAvailabilityResult | null>(null)
  const debounceScheduleCheck = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Decline & Reschedule Modal State
  const [declineModalMeeting, setDeclineModalMeeting] = useState<MeetingItem | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [proposedTime, setProposedTime] = useState('')
  const [submittingRsvp, setSubmittingRsvp] = useState(false)
  const [checkingDeclineCollision, setCheckingDeclineCollision] = useState(false)
  const [declineCollisionResult, setDeclineCollisionResult] = useState<CalendarAvailabilityResult | null>(null)
  const debounceDeclineCheck = useRef<ReturnType<typeof setTimeout> | null>(null)

  // In-Call state simulation
  const [isMuted, setIsMuted] = useState(false)
  const [isVideoOff, setIsVideoOff] = useState(false)
  const [liveTranscriptionActive, setLiveTranscriptionActive] = useState(true)

  // Notes Editor
  const [notesDraft, setNotesDraft] = useState('')
  const [savingNotes, setSavingNotes] = useState(false)

  // Calendar Month State
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const showToast = (text: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToastMessage({ type, text })
    setTimeout(() => {
      setToastMessage((prev) => (prev?.text === text ? null : prev))
    }, 4500)
  }

  const loadMeetings = async () => {
    setLoading(true)
    try {
      const res = await meetingsApi.listMeetings()
      setMeetings(res.items || [])
    } catch (err) {
      console.error('Failed to load meetings:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadDirectory = async () => {
    try {
      const users = await usersApi.getDirectory()
      setDirectoryUsers(users || [])
    } catch (err) {
      console.error('Failed to load directory:', err)
    }
  }

  const loadRecentNotifications = async () => {
    setLoadingNotifs(true)
    try {
      const items = await notificationsApi.listNotifications()
      setNotifications(items || [])
    } catch (err) {
      console.error('Failed to load notifications:', err)
    } finally {
      setLoadingNotifs(false)
    }
  }

  useEffect(() => {
    loadMeetings()
    loadDirectory()
    loadRecentNotifications()
  }, [])

  // Sync with Calendar API simulation
  const handleSyncCalendar = () => {
    setCalendarSyncing(true)
    setTimeout(() => {
      setCalendarSyncing(false)
      setCalendarSyncedAt(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
      loadMeetings()
      showToast('Synced with Google Calendar API & Microsoft Exchange (0 conflicts found)', 'info')
    }, 800)
  }

  // Live Collision Checking for Schedule Modal
  useEffect(() => {
    if (!showScheduleModal || !scheduledAt) {
      setCollisionResult(null)
      return
    }

    if (debounceScheduleCheck.current) {
      clearTimeout(debounceScheduleCheck.current)
    }

    debounceScheduleCheck.current = setTimeout(async () => {
      setCheckingCollision(true)
      try {
        const res = await meetingsApi.checkAvailability({
          scheduled_at: new Date(scheduledAt).toISOString(),
          duration_minutes: parseInt(duration, 10) || 30,
          attendee_ids: selectedAttendeeIds,
        })
        setCollisionResult(res)
      } catch (err) {
        console.error('Failed to check collision:', err)
      } finally {
        setCheckingCollision(false)
      }
    }, 350)

    return () => {
      if (debounceScheduleCheck.current) clearTimeout(debounceScheduleCheck.current)
    }
  }, [scheduledAt, duration, selectedAttendeeIds, showScheduleModal])

  // Live Collision Checking for Decline / Reschedule Modal
  useEffect(() => {
    if (!declineModalMeeting || !proposedTime) {
      setDeclineCollisionResult(null)
      return
    }

    if (debounceDeclineCheck.current) {
      clearTimeout(debounceDeclineCheck.current)
    }

    debounceDeclineCheck.current = setTimeout(async () => {
      setCheckingDeclineCollision(true)
      try {
        const res = await meetingsApi.checkAvailability({
          scheduled_at: new Date(proposedTime).toISOString(),
          duration_minutes: declineModalMeeting.duration_minutes,
          attendee_ids: declineModalMeeting.attendee_ids,
          exclude_meeting_id: declineModalMeeting.id,
        })
        setDeclineCollisionResult(res)
      } catch (err) {
        console.error('Failed to check proposed time collision:', err)
      } finally {
        setCheckingDeclineCollision(false)
      }
    }, 350)

    return () => {
      if (debounceDeclineCheck.current) clearTimeout(debounceDeclineCheck.current)
    }
  }, [proposedTime, declineModalMeeting])

  // Export iCal .ics
  const handleExportIcs = (meeting?: MeetingItem) => {
    const targetMeetings = meeting ? [meeting] : meetings
    let icsContent = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Hyperrealm AI Workspace//Meetings//EN\n"

    targetMeetings.forEach((m) => {
      const dtStart = new Date(m.scheduled_at).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
      const endDate = new Date(new Date(m.scheduled_at).getTime() + m.duration_minutes * 60000)
      const dtEnd = endDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'

      icsContent += "BEGIN:VEVENT\n"
      icsContent += `UID:${m.id}@hyperrealm.io\n`
      icsContent += `SUMMARY:${m.title}\n`
      icsContent += `DESCRIPTION:${m.description || m.type || 'Hyperrealm Meeting'}\n`
      icsContent += `DTSTART:${dtStart}\n`
      icsContent += `DTEND:${dtEnd}\n`
      icsContent += `LOCATION:${m.location || 'Virtual Google Meet'}\n`
      icsContent += "END:VEVENT\n"
    })

    icsContent += "END:VCALENDAR"

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', meeting ? `${meeting.title.replace(/\s+/g, '_')}.ics` : 'Hyperrealm_Calendar.ics')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Create Meeting
  const handleCreateMeeting = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !scheduledAt) return

    if (collisionResult && !collisionResult.available) {
      const confirmCollide = window.confirm(
        `Calendar Collision Alert:\n${collisionResult.message}.\nDo you still want to force schedule this meeting?`
      )
      if (!confirmCollide) return
    }

    setSaving(true)
    try {
      const agenda = agendaText
        ? agendaText.split('\n').map((s) => s.trim()).filter(Boolean)
        : ['Technical Discussion', 'Architecture Alignments', 'Next Steps']

      await meetingsApi.createMeeting({
        title: title.trim(),
        type,
        scheduled_at: new Date(scheduledAt).toISOString(),
        duration_minutes: parseInt(duration, 10) || 30,
        attendee_ids: selectedAttendeeIds,
        agenda,
        force: Boolean(collisionResult && !collisionResult.available),
      })

      setTitle('')
      setScheduledAt('')
      setAgendaText('')
      setSelectedAttendeeIds([])
      setCollisionResult(null)
      setShowScheduleModal(false)
      await loadMeetings()
      showToast(
        selectedAttendeeIds.length > 0
          ? `Meeting scheduled! Invitations sent to ${selectedAttendeeIds.length} participant(s).`
          : 'Meeting scheduled successfully!'
      )
    } catch (err: any) {
      showToast(err?.message || 'Failed to schedule meeting', 'error')
    } finally {
      setSaving(false)
    }
  }

  // RSVP: Accept
  const handleAcceptRsvp = async (meetingId: string) => {
    try {
      const res = await meetingsApi.rsvpMeeting(meetingId, { action: 'accept' })
      showToast('Invitation accepted! Meeting confirmed on your calendar.')
      setMeetings((prev) => prev.map((m) => (m.id === meetingId ? res.meeting : m)))
    } catch (err: any) {
      showToast(err?.message || 'Failed to accept invitation', 'error')
    }
  }

  // RSVP: Open Decline Modal
  const handleOpenDeclineModal = (meeting: MeetingItem) => {
    setDeclineModalMeeting(meeting)
    setRejectionReason('')
    // Default proposed time to next day or +2 hours
    const nextSlot = new Date(new Date(meeting.scheduled_at).getTime() + 2 * 3600000)
    // Format to YYYY-MM-DDTHH:mm
    const tzOffset = nextSlot.getTimezoneOffset() * 60000
    const localIso = new Date(nextSlot.getTime() - tzOffset).toISOString().slice(0, 16)
    setProposedTime(localIso)
    setDeclineCollisionResult(null)
  }

  // RSVP: Submit Decline with reason & proposed time -> auto-reschedule
  const handleSubmitDeclineAndReschedule = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!declineModalMeeting) return
    if (!rejectionReason.trim()) {
      showToast('Please specify the reason why you cannot attend.', 'error')
      return
    }
    if (!proposedTime) {
      showToast('Please specify the time when you will be available.', 'error')
      return
    }

    if (declineCollisionResult && !declineCollisionResult.available) {
      showToast(
        `Collision Alert: Your proposed time overlaps with ${declineCollisionResult.conflicts[0]?.title || 'another call'}. Please select an open slot.`,
        'error'
      )
      return
    }

    setSubmittingRsvp(true)
    try {
      const res = await meetingsApi.rsvpMeeting(declineModalMeeting.id, {
        action: 'reject',
        rejection_reason: rejectionReason.trim(),
        proposed_time: new Date(proposedTime).toISOString(),
      })

      showToast(
        `Meeting auto-rescheduled to ${new Date(proposedTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} without collisions! Organiser notified.`
      )
      setMeetings((prev) => prev.map((m) => (m.id === declineModalMeeting.id ? res.meeting : m)))
      setDeclineModalMeeting(null)
    } catch (err: any) {
      showToast(err?.message || 'Failed to reschedule meeting', 'error')
    } finally {
      setSubmittingRsvp(false)
    }
  }

  // Open Notes Modal
  const handleOpenNotes = (meeting: MeetingItem) => {
    setSelectedMeetingNotes(meeting)
    setNotesDraft(meeting.notes || DEFAULT_TRANSCRIPTS.default.transcript)
  }

  // Save Notes
  const handleSaveNotes = async () => {
    if (!selectedMeetingNotes) return
    setSavingNotes(true)
    try {
      await meetingsApi.updateMeeting(selectedMeetingNotes.id, { notes: notesDraft })
      setMeetings((prev) =>
        prev.map((m) => (m.id === selectedMeetingNotes.id ? { ...m, notes: notesDraft } : m))
      )
      setSelectedMeetingNotes((prev) => (prev ? { ...prev, notes: notesDraft } : null))
      showToast('Transcript and notes saved successfully.')
    } catch (err) {
      console.error('Failed to save notes:', err)
      showToast('Failed to save notes', 'error')
    } finally {
      setSavingNotes(false)
    }
  }

  // Filter strictly to meetings relevant to the logged-in user (as organiser or attendee)
  const userRelevantMeetings = useMemo(() => {
    if (!user?.id) return meetings
    return meetings.filter(
      (m) => m.organiser_id === user.id || m.attendee_ids?.includes(user.id)
    )
  }, [meetings, user?.id])

  // Pending Invites awaiting current user's RSVP
  const pendingInvites = useMemo(() => {
    if (!user?.id) return []
    return userRelevantMeetings.filter(
      (m) =>
        m.attendee_ids?.includes(user.id) &&
        m.attendee_status?.[user.id] === 'pending'
    )
  }, [userRelevantMeetings, user])

  // Filtered Meetings
  const filteredMeetings = useMemo(() => {
    const now = Date.now()
    const todayStr = new Date().toDateString()

    return userRelevantMeetings.filter((m) => {
      const meetTime = new Date(m.scheduled_at).getTime()
      const meetDateStr = new Date(m.scheduled_at).toDateString()

      if (filterType === 'pending_rsvp') {
        return user?.id && m.attendee_ids?.includes(user.id) && m.attendee_status?.[user.id] === 'pending'
      }
      if (filterType === 'upcoming') {
        return meetTime >= now
      }
      if (filterType === 'today') {
        return meetDateStr === todayStr
      }
      if (filterType === 'with_notes') {
        return Boolean(m.notes && m.notes.trim().length > 0)
      }
      return true
    })
  }, [userRelevantMeetings, filterType, user])

  // Calendar Days Calculation
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)

    const daysInMonth = lastDay.getDate()
    const startDayIndex = firstDay.getDay() // 0 = Sun

    const days: { date: Date; isCurrentMonth: boolean; meetings: MeetingItem[] }[] = []

    // Padding before
    for (let i = startDayIndex - 1; i >= 0; i--) {
      const d = new Date(year, month, -i)
      days.push({ date: d, isCurrentMonth: false, meetings: [] })
    }

    // Month days
    for (let i = 1; i <= daysInMonth; i++) {
      const d = new Date(year, month, i)
      const dayMeetings = userRelevantMeetings.filter((m) => {
        const md = new Date(m.scheduled_at)
        return (
          md.getDate() === d.getDate() &&
          md.getMonth() === d.getMonth() &&
          md.getFullYear() === d.getFullYear()
        )
      })
      days.push({ date: d, isCurrentMonth: true, meetings: dayMeetings })
    }

    // Padding after
    const remaining = 35 - days.length
    if (remaining > 0) {
      for (let i = 1; i <= remaining; i++) {
        const d = new Date(year, month + 1, i)
        days.push({ date: d, isCurrentMonth: false, meetings: [] })
      }
    }

    return days
  }, [currentMonth, userRelevantMeetings])

  // Helper to format ISO to datetime-local value
  const toLocalInputValue = (isoStr: string) => {
    try {
      const d = new Date(isoStr)
      const tzOffset = d.getTimezoneOffset() * 60000
      return new Date(d.getTime() - tzOffset).toISOString().slice(0, 16)
    } catch {
      return ''
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Toast Banner */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 animate-in fade-in slide-in-from-top duration-300 max-w-md">
          <div
            className={`p-3.5 rounded-2xl shadow-xl border backdrop-blur-md flex items-center gap-3 text-xs font-medium text-white ${
              toastMessage.type === 'error'
                ? 'bg-rose-950/90 border-rose-500/40'
                : toastMessage.type === 'info'
                ? 'bg-cyan-950/90 border-cyan-500/40'
                : 'bg-emerald-950/90 border-emerald-500/40'
            }`}
          >
            {toastMessage.type === 'error' ? (
              <AlertCircle className="h-4 w-4 text-rose-400 flex-shrink-0" />
            ) : toastMessage.type === 'info' ? (
              <CalendarCheck className="h-4 w-4 text-cyan-400 flex-shrink-0" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
            )}
            <span className="flex-1">{toastMessage.text}</span>
            <button
              onClick={() => setToastMessage(null)}
              className="text-white/60 hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-7">
        {/* ─── 1. HEADER & CONTROLS ─────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-cyan-500/15 via-blue-500/15 to-purple-500/15 border border-cyan-200 dark:border-cyan-500/30 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
                <CalendarDays className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  Meetings & Calendar
                </h1>
                <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-0.5">
                  Invites with RSVP response, auto-rescheduling, calendar collision detection, and video rooms.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleSyncCalendar}
              disabled={calendarSyncing}
              className="gap-2 text-xs h-9 px-3.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-cyan-400 ${calendarSyncing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Sync Calendar API</span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono">({calendarSyncedAt})</span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleExportIcs()}
              className="gap-1.5 text-xs h-9 px-3.5"
              title="Export all meetings to iCal (.ics)"
            >
              <Download className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Export .ICS</span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowNotificationsModal(true)}
              className="gap-1.5 text-xs h-9 px-3.5 relative"
              title="Recent Meeting Notifications"
            >
              <Bell className="h-3.5 w-3.5 text-purple-400" />
              <span className="hidden sm:inline">Alerts</span>
              {pendingInvites.length > 0 && (
                <span className="h-2 w-2 rounded-full bg-rose-500 ring-2 ring-[var(--bg-surface)] animate-pulse" />
              )}
            </Button>

            <Button
              size="sm"
              variant="gemini"
              onClick={() => setShowScheduleModal(true)}
              className="gap-2 text-xs h-9 px-4 rounded-xl shadow-md"
            >
              <Plus className="h-3.5 w-3.5" />
              Schedule Call
            </Button>
          </div>
        </div>

        {/* ─── 2. CALENDAR API CONNECTIVITY BANNER ─────────────────────── */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-50/80 via-blue-50/50 to-purple-50/50 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-950 border border-cyan-200 dark:border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs shadow-xs dark:shadow-none">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <div>
              <span className="font-semibold text-[var(--text-primary)]">Calendar API Conflict Protection Active</span>
              <span className="text-[var(--text-muted)] ml-2">
                Automatic overlap collision detection • Instant auto-reschedule on decline • Live Google/Exchange sync
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5 font-mono">
              <Video className="h-3.5 w-3.5 text-cyan-400" /> Auto-Google Meet Link Ready
            </span>
            <span className="flex items-center gap-1.5 font-mono">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" /> 0-Collision Scheduler
            </span>
          </div>
        </div>

        {/* ─── 3. PENDING INVITATIONS ACTION BANNER ─────────────────────── */}
        {pendingInvites.length > 0 && (
          <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-purple-500/10 to-indigo-500/10 border-2 border-amber-500/40 dark:border-amber-500/30 shadow-lg space-y-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-xl bg-amber-500/20 text-amber-500 dark:text-amber-400 flex items-center justify-center font-bold">
                  <CalendarCheck className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                    Pending Meeting Invitations Awaiting Your RSVP
                    <Badge variant="amber" size="sm">
                      {pendingInvites.length} action{pendingInvites.length > 1 ? 's' : ''} needed
                    </Badge>
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)]">
                    You have been invited to the following call(s). Accept or reject with a reason and proposed time to auto-reschedule.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              {pendingInvites.map((m) => {
                const date = new Date(m.scheduled_at)
                return (
                  <div
                    key={m.id}
                    className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-sm space-y-3 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-bold text-[var(--text-primary)] leading-tight">{m.title}</h4>
                        <Badge variant="cyan" size="sm" className="capitalize text-[10px]">
                          {m.type || 'General'}
                        </Badge>
                      </div>

                      <div className="mt-2 space-y-1 text-xs text-[var(--text-secondary)]">
                        <div className="flex items-center gap-1.5 font-medium">
                          <Clock className="h-3.5 w-3.5 text-cyan-400" />
                          <span>
                            {date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} at{' '}
                            {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({m.duration_minutes}m)
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[var(--text-muted)] text-[11px]">
                          <Crown className="h-3 w-3 text-amber-400" />
                          <span>Organised by: <strong className="text-[var(--text-primary)]">{m.organiser_name || m.organiser_id}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleOpenDeclineModal(m)}
                        className="text-xs h-8 px-3 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/30"
                      >
                        Decline & Reschedule
                      </Button>
                      <Button
                        size="sm"
                        variant="gemini"
                        onClick={() => handleAcceptRsvp(m.id)}
                        className="text-xs h-8 px-3.5 rounded-xl gap-1.5"
                      >
                        <Check className="h-3.5 w-3.5" />
                        Accept Call
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ─── 4. VIEW CONTROLS & FILTER TABS ──────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] flex-wrap">
            <button
              onClick={() => setFilterType('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterType === 'all'
                  ? 'bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              All Calls ({meetings.length})
            </button>
            <button
              onClick={() => setFilterType('pending_rsvp')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                filterType === 'pending_rsvp'
                  ? 'bg-[var(--bg-surface)] text-amber-400 shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              <span>Needs My RSVP</span>
              {pendingInvites.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500 text-black font-bold">
                  {pendingInvites.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setFilterType('upcoming')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterType === 'upcoming'
                  ? 'bg-[var(--bg-surface)] text-cyan-400 shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Upcoming Calls
            </button>
            <button
              onClick={() => setFilterType('today')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterType === 'today'
                  ? 'bg-[var(--bg-surface)] text-indigo-400 shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setFilterType('with_notes')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterType === 'with_notes'
                  ? 'bg-[var(--bg-surface)] text-purple-400 shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Transcribed Notes
            </button>
          </div>

          <div className="flex items-center gap-1.5 bg-[var(--bg-elevated)] p-1 rounded-xl border border-[var(--border-default)]">
            <button
              onClick={() => setViewMode('schedule')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                viewMode === 'schedule'
                  ? 'bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              Calls List
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                viewMode === 'calendar'
                  ? 'bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              <CalendarIcon className="h-3.5 w-3.5" />
              Calendar View
            </button>
          </div>
        </div>

        {/* ─── 5. MAIN CONTENT: SCHEDULE LIST OR CALENDAR ──────────────── */}
        {viewMode === 'calendar' ? (
          /* CALENDAR MONTH VIEW */
          <Card className="border-[var(--border-default)] p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-[var(--text-primary)]">
                {currentMonth.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
              </h2>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 px-2 text-xs"
                  onClick={() => setCurrentMonth(new Date())}
                >
                  Today
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-7 gap-2">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
                <div key={d} className="text-center text-[11px] font-semibold text-[var(--text-muted)] py-1">
                  {d}
                </div>
              ))}

              {calendarDays.map((cell, idx) => {
                const isToday = cell.date.toDateString() === new Date().toDateString()
                return (
                  <div
                    key={idx}
                    className={`min-h-[90px] p-2 rounded-xl border transition-all ${
                      cell.isCurrentMonth
                        ? 'bg-[var(--bg-surface)] border-[var(--border-subtle)]'
                        : 'bg-[var(--bg-elevated)]/40 border-transparent opacity-40'
                    } ${isToday ? 'border-cyan-500/50 ring-1 ring-cyan-500/30' : ''}`}
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[11px] font-mono ${
                          isToday ? 'font-bold text-cyan-400' : 'text-[var(--text-muted)]'
                        }`}
                      >
                        {cell.date.getDate()}
                      </span>
                      {cell.meetings.length > 0 && (
                        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                      )}
                    </div>

                    <div className="mt-1.5 space-y-1">
                      {cell.meetings.slice(0, 2).map((m) => (
                        <button
                          key={m.id}
                          onClick={() => handleOpenNotes(m)}
                          className="w-full text-left truncate px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-[10px] text-cyan-300 hover:bg-cyan-500/20 transition-colors"
                        >
                          {new Date(m.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}{' '}
                          {m.title}
                        </button>
                      ))}
                      {cell.meetings.length > 2 && (
                        <span className="text-[9px] text-[var(--text-muted)] block">
                          +{cell.meetings.length - 2} more
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        ) : (
          /* CALLS & SCHEDULE LIST */
          <div className="space-y-3.5">
            {loading ? (
              <div className="p-12 text-center text-sm text-[var(--text-muted)] animate-pulse">
                <RefreshCw className="h-6 w-6 animate-spin text-cyan-400 mx-auto mb-2" />
                Loading calendar meetings and scheduled calls...
              </div>
            ) : filteredMeetings.length === 0 ? (
              <Card className="p-12 text-center border-dashed">
                <CalendarIcon className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">No calls found</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto">
                  No scheduled calls match the selected filter. Click &ldquo;Schedule Call&rdquo; to create a new meeting.
                </p>
                <Button
                  size="sm"
                  variant="gemini"
                  onClick={() => setShowScheduleModal(true)}
                  className="mt-4 text-xs h-8 px-3"
                >
                  <Plus className="h-3 w-3 mr-1" /> Schedule Call
                </Button>
              </Card>
            ) : (
              filteredMeetings.map((m) => {
                const date = new Date(m.scheduled_at)
                const isUpcoming = date.getTime() > Date.now()
                const hasNotes = Boolean(m.notes && m.notes.trim().length > 0)
                const isPendingForMe = Boolean(
                  user?.id &&
                  m.attendee_ids?.includes(user.id) &&
                  m.attendee_status?.[user.id] === 'pending'
                )

                return (
                  <Card
                    key={m.id}
                    className={`p-5 rounded-2xl transition-all duration-200 group ${
                      isPendingForMe
                        ? 'border-amber-500/50 dark:border-amber-500/40 bg-amber-500/5'
                        : 'hover:border-cyan-500/40'
                    }`}
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      {/* Left: Meeting Info */}
                      <div className="flex items-start gap-4 min-w-0">
                        <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-cyan-500/15 via-blue-500/10 to-indigo-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 flex-shrink-0">
                          <Video className="h-5 w-5" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-bold text-[var(--text-primary)] truncate">
                              {m.title}
                            </h3>

                            {/* Meeting Status Badges */}
                            {m.status === 'rescheduled' ? (
                              <Badge variant="violet" size="sm">
                                Auto-Rescheduled
                              </Badge>
                            ) : m.status === 'pending' ? (
                              <Badge variant="amber" size="sm">
                                Pending RSVP
                              </Badge>
                            ) : (
                              <Badge variant={isUpcoming ? 'cyan' : 'default'} size="sm">
                                {isUpcoming ? 'Confirmed Call' : 'Completed'}
                              </Badge>
                            )}

                            <Badge variant="indigo" size="sm" className="capitalize">
                              {m.type || 'General'}
                            </Badge>

                            {hasNotes && (
                              <Badge variant="violet" size="sm" className="gap-1">
                                <Sparkles className="h-2.5 w-2.5" /> Transcribed
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] mt-1.5 flex-wrap">
                            <span className="flex items-center gap-1.5 font-medium text-[var(--text-secondary)]">
                              <Clock className="h-3.5 w-3.5 text-cyan-400" />
                              {date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} at{' '}
                              {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({m.duration_minutes}m)
                            </span>
                            <span className="flex items-center gap-1 text-[var(--text-muted)]">
                              <Crown className="h-3 w-3 text-amber-400" />
                              Organiser: <span className="font-medium text-[var(--text-primary)]">{m.organiser_name || m.organiser_id}</span>
                            </span>
                            <span className="text-cyan-400 font-mono text-[11px]">
                              meet.google.com/hyp-{m.id.slice(-4)}
                            </span>
                          </div>

                          {/* Auto-Rescheduled Note Banner */}
                          {m.status === 'rescheduled' && m.rejection_reason && (
                            <div className="mt-2.5 p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-300 flex items-start gap-2">
                              <RefreshCw className="h-3.5 w-3.5 text-purple-400 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-semibold">Automatically Rescheduled: </span>
                                <span>&ldquo;{m.rejection_reason}&rdquo;</span>
                              </div>
                            </div>
                          )}

                          {/* Attendees with RSVP Status */}
                          <div className="mt-2.5 flex items-center gap-2 flex-wrap text-xs">
                            <span className="text-[11px] font-semibold text-[var(--text-muted)] flex items-center gap-1">
                              <Users className="h-3 w-3" /> Attendees:
                            </span>
                            {m.attendee_ids && m.attendee_ids.length > 0 ? (
                              m.attendee_ids.map((aid) => {
                                const name = m.attendee_names?.[aid] || aid
                                const rsvpStatus = m.attendee_status?.[aid] || 'pending'
                                return (
                                  <span
                                    key={aid}
                                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                                      rsvpStatus === 'accepted'
                                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                                        : rsvpStatus === 'rejected'
                                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                                        : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                                    }`}
                                  >
                                    <span
                                      className={`h-1.5 w-1.5 rounded-full ${
                                        rsvpStatus === 'accepted'
                                          ? 'bg-emerald-400'
                                          : rsvpStatus === 'rejected'
                                          ? 'bg-rose-400'
                                          : 'bg-amber-400 animate-pulse'
                                      }`}
                                    />
                                    <span>{name}</span>
                                    <span className="opacity-70 text-[9px]">
                                      ({rsvpStatus === 'accepted' ? 'Accepted' : rsvpStatus === 'rejected' ? 'Declined' : 'Awaiting RSVP'})
                                    </span>
                                  </span>
                                )
                              })
                            ) : (
                              <span className="text-[11px] text-[var(--text-muted)]">Open Team Call</span>
                            )}
                          </div>

                          {/* Agenda tags */}
                          {m.agenda && m.agenda.length > 0 && (
                            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">
                                Agenda:
                              </span>
                              {m.agenda.map((topic, i) => (
                                <span
                                  key={i}
                                  className="text-[10px] px-2 py-0.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)]"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right: Actions */}
                      <div className="flex items-center gap-2.5 flex-shrink-0 self-end lg:self-center flex-wrap">
                        {/* If current user is invited and hasn't responded */}
                        {isPendingForMe && (
                          <div className="flex items-center gap-1.5 bg-amber-500/10 p-1 rounded-xl border border-amber-500/30">
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleOpenDeclineModal(m)}
                              className="h-8 text-xs px-2.5 bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30"
                            >
                              Decline & Reschedule
                            </Button>
                            <Button
                              size="sm"
                              variant="gemini"
                              onClick={() => handleAcceptRsvp(m.id)}
                              className="h-8 text-xs px-3 gap-1"
                            >
                              <Check className="h-3 w-3" /> Accept
                            </Button>
                          </div>
                        )}

                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleExportIcs(m)}
                          className="h-8 text-xs px-2.5 gap-1.5"
                          title="Export to iCal / Outlook"
                        >
                          <Download className="h-3.5 w-3.5 text-indigo-400" />
                          .ics
                        </Button>

                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenNotes(m)}
                          className="h-8 text-xs px-3 gap-1.5 border-purple-500/20 hover:border-purple-500/40 text-purple-300"
                        >
                          <FileText className="h-3.5 w-3.5 text-purple-400" />
                          Notes
                        </Button>

                        <Button
                          size="sm"
                          variant="gemini"
                          onClick={() => setActiveCallMeeting(m)}
                          className="h-8 text-xs px-3.5 gap-1.5 shadow-sm"
                        >
                          <Video className="h-3.5 w-3.5" />
                          Join Call
                        </Button>
                      </div>
                    </div>
                  </Card>
                )
              })
            )}
          </div>
        )}

        {/* ─── 6. MODAL: DECLINE & AUTO-RESCHEDULE CALL ─────────────────── */}
        {declineModalMeeting && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
            <Card className="w-full max-w-lg p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl">
              <div className="flex items-center justify-between mb-4 border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="h-9 w-9 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 font-bold">
                    <CalendarDays className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[var(--text-primary)]">Decline & Propose Time</h3>
                    <p className="text-xs text-[var(--text-muted)]">
                      {declineModalMeeting.title} • Organiser: {declineModalMeeting.organiser_name || declineModalMeeting.organiser_id}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setDeclineModalMeeting(null)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleSubmitDeclineAndReschedule} className="space-y-4">
                <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-300 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                    Automated Rescheduling Policy
                  </div>
                  <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
                    Specify the reason you cannot attend and the time you will be available. Hyperrealm will check calendar availability for all participants and automatically reschedule the meeting.
                  </p>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                    Reason for Rejection *
                  </label>
                  <textarea
                    rows={2}
                    required
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="e.g. Overlapping with customer architecture review; urgent incident triage"
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                    Available Time for Rescheduling *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={proposedTime}
                    onChange={(e) => setProposedTime(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                  />
                </div>

                {/* Calendar Collision Live Status for Proposed Time */}
                {checkingDeclineCollision ? (
                  <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center gap-2 text-xs text-[var(--text-muted)] animate-pulse">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                    Verifying calendar API availability for all participants...
                  </div>
                ) : declineCollisionResult && !declineCollisionResult.available ? (
                  <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 space-y-2">
                    <div className="font-semibold flex items-center gap-1.5 text-rose-400">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Calendar Collision Alert:
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      {declineCollisionResult.message}. The proposed time conflicts with participants&apos; calendar.
                    </p>
                    {declineCollisionResult.suggested_slots && declineCollisionResult.suggested_slots.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] uppercase font-bold text-rose-400 block mb-1">
                          Available Conflict-Free Alternative Slots:
                        </span>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {declineCollisionResult.suggested_slots.map((slot, idx) => (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => setProposedTime(toLocalInputValue(slot))}
                              className="px-2 py-1 rounded-md bg-rose-950/40 border border-rose-500/40 text-[10px] text-rose-200 hover:bg-rose-500/20 transition-all font-mono"
                            >
                              {new Date(slot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({new Date(slot).toLocaleDateString([], { month: 'short', day: 'numeric' })})
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : declineCollisionResult && declineCollisionResult.available ? (
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span>0 Calendar Collisions. All participants are free at this proposed time.</span>
                  </div>
                ) : null}

                <div className="flex justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setDeclineModalMeeting(null)}
                    disabled={submittingRsvp}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="gemini"
                    loading={submittingRsvp}
                    disabled={Boolean(declineCollisionResult && !declineCollisionResult.available)}
                    className="gap-1.5 text-xs px-4"
                  >
                    <ArrowRight className="h-3.5 w-3.5" />
                    Confirm & Auto-Reschedule
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* ─── 7. MODAL: SCHEDULE NEW CALL ─────────────────────────────── */}
        {showScheduleModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-xl p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                    <CalendarDays className="h-4 w-4" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-[var(--text-primary)]">Schedule Meeting or Call</h2>
                    <p className="text-xs text-[var(--text-muted)]">
                      Automatic calendar invite, RSVP notifications, and collision prevention
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateMeeting} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                    Meeting Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Passkeys Architecture & Security Alignment"
                    className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                  />
                </div>

                {/* Attendee / User Selector */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-semibold text-[var(--text-secondary)] block">
                      Invite Team Member(s) / Attendees
                    </label>
                    <span className="text-[11px] text-[var(--text-muted)]">
                      {selectedAttendeeIds.length} selected (they will be notified to accept/reject)
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] max-h-36 overflow-y-auto space-y-1.5">
                    {directoryUsers.length === 0 ? (
                      <div className="text-xs text-[var(--text-muted)] p-2 text-center">Loading colleagues...</div>
                    ) : (
                      directoryUsers
                        .filter((u) => u.id !== user?.id)
                        .map((colleague) => {
                          const isSelected = selectedAttendeeIds.includes(colleague.id)
                          return (
                            <button
                              key={colleague.id}
                              type="button"
                              onClick={() => {
                                setSelectedAttendeeIds((prev) =>
                                  isSelected ? prev.filter((id) => id !== colleague.id) : [...prev, colleague.id]
                                )
                              }}
                              className={`w-full flex items-center justify-between p-2 rounded-lg text-left text-xs transition-colors ${
                                isSelected
                                  ? 'bg-cyan-500/15 border border-cyan-500/40 text-cyan-300 font-semibold'
                                  : 'hover:bg-[var(--bg-surface)] text-[var(--text-primary)]'
                              }`}
                            >
                              <div className="flex items-center gap-2 truncate">
                                <div className="h-6 w-6 rounded-full bg-cyan-600/30 text-cyan-300 flex items-center justify-center text-[10px] font-bold">
                                  {colleague.name[0] || 'U'}
                                </div>
                                <div className="truncate">
                                  <span className="block truncate">{colleague.name}</span>
                                  <span className="text-[10px] text-[var(--text-muted)] font-normal block truncate">
                                    {colleague.job_title || colleague.role || colleague.email}
                                  </span>
                                </div>
                              </div>
                              <span
                                className={`h-4 w-4 rounded-md border flex items-center justify-center flex-shrink-0 ${
                                  isSelected
                                    ? 'bg-cyan-500 border-cyan-400 text-black'
                                    : 'border-[var(--border-subtle)]'
                                }`}
                              >
                                {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                              </span>
                            </button>
                          )
                        })
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                      Meeting Type
                    </label>
                    <select
                      value={type}
                      onChange={(e) => setType(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                    >
                      <option value="general">Team Sync (General)</option>
                      <option value="standup">Daily Standup</option>
                      <option value="sprint_planning">Sprint Planning</option>
                      <option value="architecture">Architecture Review</option>
                      <option value="retrospective">Sprint Retrospective</option>
                      <option value="one_on_one">1-on-1 Mentorship</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Duration</label>
                    <select
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                    >
                      <option value="15">15 mins (Quick Sync)</option>
                      <option value="30">30 mins</option>
                      <option value="45">45 mins</option>
                      <option value="60">60 mins</option>
                      <option value="90">90 mins</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                    Date & Time *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={scheduledAt}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                  />
                </div>

                {/* Calendar Collision Status */}
                {checkingCollision ? (
                  <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center gap-2 text-xs text-[var(--text-muted)] animate-pulse">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                    Checking calendar API for collision...
                  </div>
                ) : collisionResult && !collisionResult.available ? (
                  <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 space-y-2">
                    <div className="font-semibold flex items-center gap-1.5 text-rose-400">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Calendar Collision Alert:
                    </div>
                    <p className="text-[11px] leading-relaxed">{collisionResult.message}</p>
                    {collisionResult.suggested_slots && collisionResult.suggested_slots.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] uppercase font-bold text-rose-400 block mb-1">
                          Suggested Free Alternative Slots:
                        </span>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {collisionResult.suggested_slots.map((slot, idx) => (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => setScheduledAt(toLocalInputValue(slot))}
                              className="px-2 py-1 rounded-md bg-rose-950/40 border border-rose-500/40 text-[10px] text-rose-200 hover:bg-rose-500/20 transition-all font-mono"
                            >
                              {new Date(slot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({new Date(slot).toLocaleDateString([], { month: 'short', day: 'numeric' })})
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : collisionResult && collisionResult.available ? (
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span>0 Calendar Collisions. All selected participants are available.</span>
                  </div>
                ) : null}

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">
                    Agenda Topics <span className="text-[var(--text-muted)] font-normal">(One per line)</span>
                  </label>
                  <textarea
                    rows={3}
                    value={agendaText}
                    onChange={(e) => setAgendaText(e.target.value)}
                    placeholder="Review zero-trust authorization gates&#10;Audit Redis cache TTL changes&#10;Confirm QA automated test coverage"
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
                  <Button type="button" variant="ghost" onClick={() => setShowScheduleModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="gemini" loading={saving}>
                    Confirm & Schedule Call
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* ─── 8. MODAL: NOTIFICATIONS / ACTIVITY LOG ──────────────────── */}
        {showNotificationsModal && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
            <Card className="w-full max-w-lg max-h-[85vh] flex flex-col bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-[var(--border-subtle)] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-[var(--text-primary)]">Meeting Notifications & Alerts</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNotificationsModal(false)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="p-4 overflow-y-auto space-y-2.5 flex-1">
                {loadingNotifs ? (
                  <div className="p-8 text-center text-xs text-[var(--text-muted)] animate-pulse">
                    Loading notifications...
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[var(--text-muted)]">No recent notifications.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 rounded-xl border text-xs space-y-1 ${
                        n.type.includes('rescheduled')
                          ? 'bg-purple-500/10 border-purple-500/30'
                          : n.type.includes('invitation')
                          ? 'bg-amber-500/10 border-amber-500/30'
                          : n.type.includes('accepted')
                          ? 'bg-emerald-500/10 border-emerald-500/30'
                          : 'bg-[var(--bg-elevated)] border-[var(--border-subtle)]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[var(--text-primary)]">{n.title}</span>
                        <span className="text-[10px] text-[var(--text-muted)]">
                          {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{n.body}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="p-3 border-t border-[var(--border-subtle)] flex justify-end">
                <Button size="sm" variant="ghost" onClick={() => setShowNotificationsModal(false)}>
                  Close
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* ─── 9. MODAL: TRANSCRIBE NOTES FROM THE MEETING ─────────────── */}
        {selectedMeetingNotes && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
            <Card className="w-full max-w-3xl max-h-[90vh] flex flex-col bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl rounded-2xl overflow-hidden">
              {/* Header */}
              <div className="p-5 border-b border-[var(--border-subtle)] flex items-center justify-between bg-gradient-to-r from-purple-50/90 via-transparent to-cyan-50/90 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-900">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
                    <Sparkles className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                      Meeting Transcribe Notes
                      <Badge variant="violet" size="sm">
                        Whisper AI Grounded
                      </Badge>
                    </h2>
                    <p className="text-xs text-[var(--text-muted)]">
                      {selectedMeetingNotes.title} • {new Date(selectedMeetingNotes.scheduled_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedMeetingNotes(null)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Body */}
              <div className="p-6 overflow-y-auto space-y-5 flex-1">
                {/* AI Executive Summary */}
                <div className="p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] space-y-2">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    AI Executive Summary
                  </h4>
                  <p className="text-xs text-[var(--text-primary)] leading-relaxed">
                    {DEFAULT_TRANSCRIPTS.default.summary}
                  </p>
                </div>

                {/* Extracted Action Items */}
                <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 space-y-2.5">
                  <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                    Detected Action Items
                  </h4>
                  <ul className="space-y-1.5">
                    {DEFAULT_TRANSCRIPTS.default.actionItems.map((item, idx) => (
                      <li key={idx} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Editable Full Transcript & Notes */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-cyan-400" />
                      Speaker Transcript & Notes
                    </label>
                    <span className="text-[11px] text-[var(--text-muted)] font-mono">
                      Real-time Speech Recognition
                    </span>
                  </div>
                  <textarea
                    rows={8}
                    value={notesDraft}
                    onChange={(e) => setNotesDraft(e.target.value)}
                    className="w-full p-3.5 font-mono text-xs rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-purple-500 leading-relaxed"
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex items-center justify-between">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(notesDraft)}
                  className="gap-1.5 text-xs h-8"
                >
                  <Copy className="h-3 w-3" />
                  Copy Transcript
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedMeetingNotes(null)}
                    className="text-xs h-8"
                  >
                    Close
                  </Button>
                  <Button
                    size="sm"
                    variant="gemini"
                    onClick={handleSaveNotes}
                    loading={savingNotes}
                    className="text-xs h-8 px-4"
                  >
                    Save Notes
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ─── 10. MODAL: LIVE VIDEO CALL ROOM SIMULATOR ────────────────── */}
        {activeCallMeeting && (
          <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-lg flex flex-col p-4 sm:p-6">
            {/* Call Header */}
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-full bg-rose-500 animate-ping" />
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                    {activeCallMeeting.title}
                    <Badge variant="rose" size="sm">
                      LIVE CALL
                    </Badge>
                  </h3>
                  <p className="text-xs text-zinc-400">
                    Google Meet ID: hyp-{activeCallMeeting.id.slice(-6)} • Secured with TLS 1.3
                  </p>
                </div>
              </div>

              <Button
                variant="destructive"
                size="sm"
                onClick={() => setActiveCallMeeting(null)}
                className="h-8 text-xs px-4 rounded-xl"
              >
                Leave Call
              </Button>
            </div>

            {/* Video Grid */}
            <div className="flex-1 py-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 min-h-0">
              {/* Tile 1: User */}
              <div className="relative rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden shadow-inner">
                {isVideoOff ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-16 w-16 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xl font-bold text-indigo-300">
                      {user?.name?.[0] || 'U'}
                    </div>
                    <p className="text-xs text-zinc-400">{user?.name || 'You'} (Camera Off)</p>
                  </div>
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-indigo-950 via-zinc-900 to-zinc-950 flex items-center justify-center">
                    <div className="text-center">
                      <div className="h-20 w-20 rounded-full bg-indigo-500/20 border-2 border-indigo-500/50 flex items-center justify-center text-2xl font-bold text-indigo-400 mx-auto mb-2 animate-pulse">
                        {user?.name?.[0] || 'U'}
                      </div>
                      <p className="text-sm font-semibold text-white">{user?.name || 'You'}</p>
                      <p className="text-xs text-indigo-400 font-mono mt-0.5">Speaking • High Definition</p>
                    </div>
                  </div>
                )}
                <div className="absolute bottom-3 left-3 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-[11px] text-white font-medium flex items-center gap-1.5">
                  {isMuted ? <MicOff className="h-3 w-3 text-rose-400" /> : <Mic className="h-3 w-3 text-emerald-400" />}
                  {user?.name || 'You'}
                </div>
              </div>

              {/* Tile 2: Carol Wu */}
              <div className="relative rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden">
                <div className="w-full h-full bg-gradient-to-br from-purple-950/60 via-zinc-900 to-zinc-950 flex items-center justify-center">
                  <div className="text-center">
                    <div className="h-20 w-20 rounded-full bg-purple-500/20 border-2 border-purple-500/40 flex items-center justify-center text-2xl font-bold text-purple-300 mx-auto mb-2">
                      CW
                    </div>
                    <p className="text-sm font-semibold text-white">Carol Wu</p>
                    <p className="text-xs text-purple-400 font-mono mt-0.5">Technical Lead</p>
                  </div>
                </div>
                <div className="absolute bottom-3 left-3 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-[11px] text-white font-medium flex items-center gap-1.5">
                  <Mic className="h-3 w-3 text-emerald-400" />
                  Carol Wu
                </div>
              </div>

              {/* Tile 3: Priya Sharma */}
              <div className="relative rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden">
                <div className="w-full h-full bg-gradient-to-br from-blue-950/60 via-zinc-900 to-zinc-950 flex items-center justify-center">
                  <div className="text-center">
                    <div className="h-20 w-20 rounded-full bg-blue-500/20 border-2 border-blue-500/40 flex items-center justify-center text-2xl font-bold text-blue-300 mx-auto mb-2">
                      PS
                    </div>
                    <p className="text-sm font-semibold text-white">Priya Sharma</p>
                    <p className="text-xs text-blue-400 font-mono mt-0.5">QA Lead</p>
                  </div>
                </div>
                <div className="absolute bottom-3 left-3 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-[11px] text-white font-medium flex items-center gap-1.5">
                  <Mic className="h-3 w-3 text-emerald-400" />
                  Priya Sharma
                </div>
              </div>
            </div>

            {/* Live Transcription Bar */}
            {liveTranscriptionActive && (
              <div className="mb-4 p-3 rounded-xl bg-zinc-900/90 border border-purple-500/30 backdrop-blur-sm flex items-center gap-3 text-xs">
                <div className="h-2 w-2 rounded-full bg-purple-400 animate-ping flex-shrink-0" />
                <span className="font-semibold text-purple-300 flex-shrink-0">Live Transcribe:</span>
                <span className="text-zinc-200 truncate">
                  &ldquo;Priya Sharma: Let&apos;s ensure the automated test suite includes Redis failover regression coverage before the release.&rdquo;
                </span>
              </div>
            )}

            {/* Bottom Controls Bar */}
            <div className="pt-2 flex items-center justify-center gap-3">
              <button
                onClick={() => setIsMuted(!isMuted)}
                className={`h-11 w-11 rounded-full flex items-center justify-center text-white transition-colors ${
                  isMuted ? 'bg-rose-600 hover:bg-rose-500' : 'bg-zinc-800 hover:bg-zinc-700'
                }`}
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </button>

              <button
                onClick={() => setIsVideoOff(!isVideoOff)}
                className={`h-11 w-11 rounded-full flex items-center justify-center text-white transition-colors ${
                  isVideoOff ? 'bg-rose-600 hover:bg-rose-500' : 'bg-zinc-800 hover:bg-zinc-700'
                }`}
                title={isVideoOff ? 'Turn Video On' : 'Turn Video Off'}
              >
                {isVideoOff ? <VideoOff className="h-5 w-5" /> : <Video className="h-5 w-5" />}
              </button>

              <button
                onClick={() => setLiveTranscriptionActive(!liveTranscriptionActive)}
                className={`px-4 h-11 rounded-full flex items-center gap-2 text-xs font-semibold transition-colors ${
                  liveTranscriptionActive
                    ? 'bg-purple-600/30 text-purple-300 border border-purple-500/50'
                    : 'bg-zinc-800 text-zinc-400'
                }`}
              >
                <Sparkles className="h-4 w-4" />
                {liveTranscriptionActive ? 'Transcribing Live' : 'Enable Transcribe'}
              </button>

              <button
                onClick={() => {
                  handleOpenNotes(activeCallMeeting)
                }}
                className="px-4 h-11 rounded-full bg-zinc-800 hover:bg-zinc-700 text-white flex items-center gap-2 text-xs font-semibold"
              >
                <FileText className="h-4 w-4 text-cyan-400" />
                View Notes
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
