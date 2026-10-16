import { useState, useEffect } from 'react'
import { CalendarDays, Clock, Video, Users, Plus, RefreshCw, X } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { meetingsApi } from '@/lib/api'
import type { MeetingItem } from '@/types'

const scrumSprints = [
  {
    id: 'sp1',
    sprint: 'Sprint 42',
    goal: 'Complete AI workspace MVP and knowledge search integration',
    start: 'Oct 14',
    end: 'Oct 27',
    velocity: 34,
    targetVelocity: 38,
    progress: 65,
    status: 'active',
  },
]

export function MeetingsPage() {
  const [meetings, setMeetings] = useState<MeetingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [title, setTitle] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [duration, setDuration] = useState('45')
  const [saving, setSaving] = useState(false)

  const loadMeetings = async () => {
    setLoading(true)
    try {
      const res = await meetingsApi.listMeetings()
      setMeetings(res.items)
    } catch (err) {
      console.error('Failed to load meetings:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMeetings()
  }, [])

  const handleCreateMeeting = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !scheduledAt) return
    setSaving(true)
    try {
      await meetingsApi.createMeeting({
        title: title.trim(),
        scheduled_at: new Date(scheduledAt).toISOString(),
        duration_minutes: parseInt(duration, 10) || 30,
      })
      setTitle('')
      setScheduledAt('')
      setShowModal(false)
      await loadMeetings()
    } catch (err: any) {
      alert(err?.message || 'Failed to schedule meeting')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
              <CalendarDays className="h-6 w-6 text-[var(--accent-indigo)]" />
              Meetings & Scrum
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Scheduled meetings, stand-ups, and sprint management backed by SQLite.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={loadMeetings} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button size="sm" onClick={() => setShowModal(true)}>
              <Plus className="h-4 w-4" />
              Schedule Meeting
            </Button>
          </div>
        </div>

        {/* Modal: Schedule Meeting */}
        {showModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-md p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-[var(--text-primary)]">Schedule Meeting</h2>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="text-zinc-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleCreateMeeting} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Title *</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Architecture Sync"
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Date & Time *</label>
                  <input
                    type="datetime-local"
                    required
                    value={scheduledAt}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Duration (minutes)</label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  >
                    <option value="15">15 mins (Standup)</option>
                    <option value="30">30 mins</option>
                    <option value="45">45 mins</option>
                    <option value="60">60 mins</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="ghost" onClick={() => setShowModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" loading={saving}>
                    Confirm & Schedule
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Sprint card */}
        <div>
          <h2 className="text-base font-semibold mb-4">Active Sprint</h2>
          {scrumSprints.map((sprint) => (
            <Card key={sprint.id} variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">{sprint.sprint}</h3>
                      <Badge variant="emerald">Active</Badge>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">{sprint.goal}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-[var(--text-muted)]">{sprint.start} → {sprint.end}</p>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      Velocity: {sprint.velocity}/{sprint.targetVelocity} pts
                    </p>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-[var(--text-secondary)]">Sprint progress</span>
                    <span className="text-[var(--accent-indigo)] font-medium">{sprint.progress}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-overlay)]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all"
                      style={{ width: `${sprint.progress}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Meetings list */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-base font-semibold">Scheduled Meetings</h2>
            <Badge variant="indigo">{meetings.length}</Badge>
          </div>
          {meetings.length === 0 ? (
            <Card className="p-8 text-center text-sm text-[var(--text-muted)] border-dashed">
              No upcoming meetings scheduled.
            </Card>
          ) : (
            <div className="space-y-3">
              {meetings.map((m) => {
                const date = new Date(m.scheduled_at)
                return (
                  <Card key={m.id} interactive className="group hover:border-indigo-500/40 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        <div
                          className="h-10 w-10 flex-shrink-0 rounded-[var(--radius-md)] flex items-center justify-center bg-indigo-500/15"
                        >
                          <Video className="h-5 w-5 text-indigo-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-semibold text-sm text-[var(--text-primary)]">{m.title}</p>
                            <Badge variant="indigo" size="sm">{m.type || 'general'}</Badge>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5 text-indigo-400" />
                              {date.toLocaleDateString()} at {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({m.duration_minutes}m)
                            </span>
                            {m.attendee_ids && m.attendee_ids.length > 0 && (
                              <span className="flex items-center gap-1">
                                <Users className="h-3.5 w-3.5" /> {m.attendee_ids.length} attendees
                              </span>
                            )}
                          </div>
                        </div>
                        <Button variant="secondary" size="sm" className="flex-shrink-0">
                          Join Call
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
