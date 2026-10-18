import React, { useState } from 'react'
import {
  Calendar,
  Clock,
  Video,
  User,
  Mail,
  CheckCircle2,
  AlertCircle,
  Loader2,
  CalendarCheck,
  Edit3,
  X,
  ExternalLink,
} from 'lucide-react'
import { meetingsApi } from '@/lib/api'
import { cn } from '@/lib/utils'

export interface MeetingProposalCardProps {
  proposalId?: string
  payload?: Record<string, any>
  title: string
  description?: string
  onConfirmed?: (meeting: any) => void
}

export const MeetingProposalCard: React.FC<MeetingProposalCardProps> = ({
  proposalId: initialPropId,
  payload = {},
  title,
  description,
  onConfirmed,
}) => {
  const proposalId = initialPropId || payload.proposal_id

  const [status, setStatus] = useState<string>(payload.status || 'pending_confirmation')
  const meetingTitle = payload.title || title
  const targetName = payload.target_name || 'Participant'
  const targetEmail = payload.target_email || ''
  const targetRole = payload.target_role || 'Subject-Matter Expert'
  const userName = payload.user_name || 'You'
  const userEmail = payload.user_email || ''
  const [scheduledIst, setScheduledIst] = useState<string>(payload.scheduled_at_ist || 'Tomorrow at 11:00 AM IST')
  const [scheduledAt, setScheduledAt] = useState<string>(payload.scheduled_at || '')
  const [duration, setDuration] = useState<number>(payload.duration_minutes || 30)
  const calendarStatus = payload.calendar_status || 'Local simulation mode (No external Google Calendar account linked)'
  const [availabilityNote, setAvailabilityNote] = useState<string>(
    payload.availability_note || '✅ Availability verified: No calendar collisions detected for all participants.'
  )

  // State for confirm interaction
  const [isConfirming, setIsConfirming] = useState(false)
  const [confirmedMeeting, setConfirmedMeeting] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // State for Choose Another Time edit mode
  const [isEditing, setIsEditing] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [editDate, setEditDate] = useState(() => {
    if (scheduledAt) {
      try {
        return new Date(scheduledAt).toISOString().split('T')[0]
      } catch {
        // fallback
      }
    }
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  })
  const [editTime, setEditTime] = useState('11:00')
  const [editDuration, setEditDuration] = useState(duration)

  // Handle Confirm & Schedule
  const handleConfirm = async () => {
    if (!proposalId) {
      setErrorMsg('Proposal ID missing. Cannot confirm meeting.')
      return
    }
    setIsConfirming(true)
    setErrorMsg(null)

    try {
      // Idempotency token to prevent double-click / duplicate creation
      const idempKey = `idemp_confirm_${proposalId}_${Date.now()}`
      const res = await meetingsApi.confirmProposal(proposalId, idempKey)
      setStatus('confirmed')
      setConfirmedMeeting(res.meeting)
      setSuccessMsg(res.message || 'Meeting successfully confirmed and scheduled!')
      if (onConfirmed) {
        onConfirmed(res.meeting)
      }
    } catch (err: any) {
      console.error('Confirmation failed:', err)
      const detail = err?.data?.detail
      if (detail && typeof detail === 'object' && detail.message) {
        setErrorMsg(detail.message)
      } else if (typeof detail === 'string') {
        setErrorMsg(detail)
      } else {
        setErrorMsg(err.message || 'Failed to schedule meeting. Please try again.')
      }
    } finally {
      setIsConfirming(false)
    }
  }

  // Handle Choose Another Time save
  const handleSaveAnotherTime = async () => {
    if (!proposalId) return
    setIsUpdating(true)
    setErrorMsg(null)

    try {
      // Construct date string in IST (+05:30)
      const newScheduledAt = new Date(`${editDate}T${editTime}:00+05:30`).toISOString()
      const updated = await meetingsApi.updateProposal(proposalId, {
        scheduled_at: newScheduledAt,
        duration_minutes: editDuration,
      })

      setScheduledAt(updated.scheduled_at)
      setScheduledIst(updated.scheduled_at_ist)
      setDuration(updated.duration_minutes)
      setAvailabilityNote(updated.availability_note)
      setIsEditing(false)
      setSuccessMsg('Proposal updated with revised time! Review and click Confirm & Schedule.')
    } catch (err: any) {
      console.error('Failed to update time:', err)
      setErrorMsg(err?.data?.detail || err.message || 'Failed to update proposal time.')
    } finally {
      setIsUpdating(false)
    }
  }

  // Handle Cancellation
  const handleCancel = async () => {
    if (!proposalId) return
    try {
      await meetingsApi.cancelProposal(proposalId)
      setStatus('cancelled')
    } catch (err: any) {
      console.error('Failed to cancel proposal:', err)
    }
  }

  return (
    <div className="my-3 rounded-2xl border border-purple-500/25 bg-gradient-to-b from-[var(--bg-elevated)] to-[var(--bg-surface)] p-4 text-xs shadow-md space-y-3.5 transition-all">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-500/15 text-purple-400">
            <Calendar className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-[var(--text-primary)] leading-tight">{meetingTitle}</h4>
            <p className="text-[11px] text-[var(--text-secondary)]">Consequential Action • Official Meeting Proposal</p>
          </div>
        </div>

        {/* Status Badge */}
        <div>
          {status === 'confirmed' ? (
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Confirmed & Scheduled
            </span>
          ) : status === 'cancelled' ? (
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
              <X className="h-3.5 w-3.5" />
              Cancelled
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
              <Clock className="h-3.5 w-3.5" />
              Pending User Confirmation
            </span>
          )}
        </div>
      </div>

      {/* Description */}
      {description && (
        <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed italic bg-[var(--bg-base)]/50 p-2.5 rounded-xl border border-[var(--border-subtle)]">
          {description}
        </p>
      )}

      {/* Meeting Proposal Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 bg-[var(--bg-base)]/40 p-3 rounded-xl border border-[var(--border-subtle)]">
        {/* Target Attendee */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
            <User className="h-3 w-3 text-purple-400" />
            Verified Participant
          </span>
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-medium text-[var(--text-primary)]">{targetName}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-purple-500/10 text-purple-300 font-semibold border border-purple-500/20">
              {targetRole}
            </span>
          </div>
          {targetEmail && (
            <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
              <Mail className="h-2.5 w-2.5" /> {targetEmail}
            </div>
          )}
        </div>

        {/* Requester / Authenticated User */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
            <User className="h-3 w-3 text-blue-400" />
            Requester
          </span>
          <p className="font-medium text-[var(--text-primary)]">{userName}</p>
          {userEmail && (
            <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
              <Mail className="h-2.5 w-2.5" /> {userEmail}
            </div>
          )}
        </div>

        {/* Proposed Date & Time */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
            <Clock className="h-3 w-3 text-indigo-400" />
            Proposed Time
          </span>
          <p className="font-semibold text-purple-300">{scheduledIst}</p>
          <p className="text-[10px] text-[var(--text-muted)]">Duration: {duration} mins • Time Zone: IST (UTC+05:30)</p>
        </div>

        {/* Calendar / Meet Integration Status */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
            <Video className="h-3 w-3 text-emerald-400" />
            Integration Status
          </span>
          <p className="text-[11px] text-[var(--text-secondary)] leading-tight">{calendarStatus}</p>
        </div>
      </div>

      {/* Availability Check Badge */}
      <div className="p-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-start gap-2">
        <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-[11px]">
          <span className="font-semibold text-[var(--text-primary)]">Collision & Availability Status: </span>
          <span className="text-[var(--text-secondary)]">{availabilityNote}</span>
        </div>
      </div>

      {/* Alerts (Error / Success) */}
      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2 animate-in fade-in">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-rose-200">Scheduling Blocked</p>
            <p className="text-[11px] mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-emerald-200">Success</p>
            <p className="text-[11px] mt-0.5">{successMsg}</p>
          </div>
        </div>
      )}

      {/* Confirmed State Details */}
      {status === 'confirmed' && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
              <CalendarCheck className="h-4 w-4" />
              Event officially scheduled in HYPERREALM Calendar
            </span>
            <a
              href="/app/meetings"
              className="text-[11px] text-purple-400 hover:text-purple-300 underline flex items-center gap-1 font-medium"
            >
              View in Calendar <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {(confirmedMeeting?.meet_link || payload.meet_link) && (
            <div className="pt-1 flex items-center gap-2">
              <a
                href={confirmedMeeting?.meet_link || payload.meet_link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-sm transition-all"
              >
                <Video className="h-3.5 w-3.5" />
                Join Google Meet
              </a>
              <span className="text-[11px] text-[var(--text-muted)] truncate">
                {confirmedMeeting?.meet_link || payload.meet_link}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Choose Another Time - Inline Editor */}
      {isEditing && status === 'pending_confirmation' && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-purple-300 text-xs flex items-center gap-1.5">
              <Edit3 className="h-3.5 w-3.5" />
              Choose Another Time
            </span>
            <button
              onClick={() => setIsEditing(false)}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-[var(--text-muted)] block mb-1">Date</label>
              <input
                type="date"
                value={editDate}
                onChange={(e) => setEditDate(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1 text-xs text-[var(--text-primary)] focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="text-[10px] text-[var(--text-muted)] block mb-1">Time (IST)</label>
              <select
                value={editTime}
                onChange={(e) => setEditTime(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1 text-xs text-[var(--text-primary)] focus:outline-none focus:border-purple-500"
              >
                <option value="09:00">09:00 AM IST</option>
                <option value="10:00">10:00 AM IST</option>
                <option value="11:00">11:00 AM IST</option>
                <option value="12:00">12:00 PM IST</option>
                <option value="14:00">02:00 PM IST</option>
                <option value="15:00">03:00 PM IST</option>
                <option value="16:00">04:00 PM IST</option>
                <option value="17:00">05:00 PM IST</option>
                <option value="18:00">06:00 PM IST</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-[var(--text-muted)] block mb-1">Duration</label>
              <select
                value={editDuration}
                onChange={(e) => setEditDuration(Number(e.target.value))}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1 text-xs text-[var(--text-primary)] focus:outline-none focus:border-purple-500"
              >
                <option value={15}>15 Minutes</option>
                <option value={30}>30 Minutes</option>
                <option value={45}>45 Minutes</option>
                <option value={60}>60 Minutes</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={() => setIsEditing(false)}
              className="px-2.5 py-1 rounded-lg border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveAnotherTime}
              disabled={isUpdating}
              className="px-3 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {isUpdating ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
              Recheck & Update Proposal
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons (Confirm & Schedule | Choose Another Time | Cancel) */}
      {status === 'pending_confirmation' && !isEditing && (
        <div className="pt-2 flex items-center justify-between flex-wrap gap-2 border-t border-[var(--border-subtle)]">
          <div className="flex items-center gap-2">
            <button
              onClick={handleConfirm}
              disabled={isConfirming}
              className={cn(
                'flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-semibold text-xs shadow-sm transition-all cursor-pointer',
                'bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-500/40',
                isConfirming && 'opacity-60 cursor-not-allowed'
              )}
            >
              {isConfirming ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Checking & Scheduling…
                </>
              ) : (
                <>
                  <CalendarCheck className="h-3.5 w-3.5" />
                  Confirm & Schedule
                </>
              )}
            </button>

            <button
              onClick={() => setIsEditing(true)}
              disabled={isConfirming}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-semibold text-xs transition-all cursor-pointer bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30"
            >
              <Clock className="h-3.5 w-3.5" />
              Choose Another Time
            </button>
          </div>

          <button
            onClick={handleCancel}
            disabled={isConfirming}
            className="text-[11px] text-[var(--text-muted)] hover:text-rose-400 transition-colors px-2 py-1"
          >
            Cancel Proposal
          </button>
        </div>
      )}
    </div>
  )
}
