import { useState, useEffect } from 'react'
import {
  CheckSquare,
  Clock,
  CheckCircle2,
  Plus,
  RefreshCw,
  XCircle,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { tasksApi } from '@/lib/api'
import type { TaskItem, ApprovalItem } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

export function TasksPage() {
  const { user } = useAuth()
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [loading, setLoading] = useState(true)
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [showNewTaskModal, setShowNewTaskModal] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskDesc, setNewTaskDesc] = useState('')
  const [newTaskPriority, setNewTaskPriority] = useState('medium')
  const [creating, setCreating] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [tRes, aRes] = await Promise.all([
        tasksApi.listTasks(),
        tasksApi.listApprovals(),
      ])
      setTasks(tRes.items)
      setApprovals(aRes.items)
    } catch (err) {
      console.error('Failed to load tasks/approvals:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleResolveApproval = async (id: string, action: 'approve' | 'reject') => {
    setResolvingId(id)
    try {
      await tasksApi.resolveApproval(id, action, `Actioned by ${user?.name || 'user'}`)
      await loadData()
    } catch (err: any) {
      alert(err?.message || 'Failed to update approval')
    } finally {
      setResolvingId(null)
    }
  }

  const handleToggleTaskStatus = async (task: TaskItem) => {
    const nextStatus = task.status === 'done' ? 'todo' : 'done'
    try {
      await tasksApi.updateTaskStatus(task.id, nextStatus)
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: nextStatus } : t))
      )
    } catch (err: any) {
      alert(err?.message || 'Failed to update task status')
    }
  }

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTaskTitle.trim()) return
    setCreating(true)
    try {
      await tasksApi.createTask({
        title: newTaskTitle.trim(),
        description: newTaskDesc.trim(),
        priority: newTaskPriority,
      })
      setNewTaskTitle('')
      setNewTaskDesc('')
      setShowNewTaskModal(false)
      await loadData()
    } catch (err: any) {
      alert(err?.message || 'Failed to create task')
    } finally {
      setCreating(false)
    }
  }

  const pendingApprovals = approvals.filter((a) => a.status === 'pending')
  const resolvedApprovals = approvals.filter((a) => a.status !== 'pending')
  const activeTasks = tasks.filter((t) => t.status !== 'done')
  const completedTasks = tasks.filter((t) => t.status === 'done')

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
              <CheckSquare className="h-6 w-6 text-[var(--accent-indigo)]" />
              Tasks & Approvals
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Real-time tasks and multi-role approval workflows backed by SQLite.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={loadData}
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button size="sm" onClick={() => setShowNewTaskModal(true)}>
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          </div>
        </div>

        {/* Modal: New Task */}
        {showNewTaskModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-md p-6 bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-2xl">
              <h2 className="text-lg font-bold mb-4 text-[var(--text-primary)]">Create Workspace Task</h2>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Title *</label>
                  <input
                    type="text"
                    required
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                    placeholder="Task summary"
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Description</label>
                  <textarea
                    rows={3}
                    value={newTaskDesc}
                    onChange={(e) => setNewTaskDesc(e.target.value)}
                    placeholder="Provide details or context..."
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1 block">Priority</label>
                  <select
                    value={newTaskPriority}
                    onChange={(e) => setNewTaskPriority(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setShowNewTaskModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={creating}>
                    Create Task
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Pending Approvals */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-base font-semibold">Pending Approvals</h2>
            <Badge variant="amber">{pendingApprovals.length}</Badge>
          </div>

          {pendingApprovals.length === 0 ? (
            <Card className="p-6 text-center text-sm text-[var(--text-muted)] border-dashed">
              No pending approvals requiring sign-off.
            </Card>
          ) : (
            <div className="space-y-3">
              {pendingApprovals.map((approval) => (
                <Card
                  key={approval.id}
                  className="border-l-4 border-l-amber-500 hover:border-amber-400/80 transition-colors"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <p className="font-semibold text-sm text-[var(--text-primary)]">
                            {approval.title}
                          </p>
                          <Badge variant="amber" size="sm">
                            Requires Sign-off
                          </Badge>
                        </div>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-2">
                          {approval.description || 'No additional details provided.'}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" /> Requested{' '}
                            {new Date(approval.requested_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      <div className="flex gap-2 flex-shrink-0">
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={resolvingId === approval.id}
                          onClick={() => handleResolveApproval(approval.id, 'reject')}
                        >
                          <XCircle className="h-3.5 w-3.5 text-rose-400" />
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          disabled={resolvingId === approval.id}
                          onClick={() => handleResolveApproval(approval.id, 'approve')}
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Approve
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Active Tasks */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-base font-semibold">Active Tasks</h2>
            <Badge variant="indigo">{activeTasks.length}</Badge>
          </div>

          {activeTasks.length === 0 ? (
            <Card className="p-6 text-center text-sm text-[var(--text-muted)] border-dashed">
              No active tasks. Click "New Task" above to add one.
            </Card>
          ) : (
            <div className="space-y-3">
              {activeTasks.map((task) => (
                <Card
                  key={task.id}
                  className="hover:border-indigo-500/30 transition-colors"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <input
                          type="checkbox"
                          checked={task.status === 'done'}
                          onChange={() => handleToggleTaskStatus(task)}
                          className="mt-1 h-4 w-4 rounded border-[var(--border-strong)] bg-[var(--bg-elevated)] text-[var(--accent-indigo)] focus:ring-[var(--accent-indigo)] cursor-pointer"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <p className="font-medium text-sm text-[var(--text-primary)]">
                              {task.title}
                            </p>
                            <Badge variant="indigo" size="sm">
                              {task.status}
                            </Badge>
                            <Badge
                              variant="default"
                              size="sm"
                              className={
                                task.priority === 'urgent' || task.priority === 'high'
                                  ? 'text-rose-400'
                                  : task.priority === 'medium'
                                  ? 'text-amber-400'
                                  : 'text-emerald-400'
                              }
                            >
                              {task.priority}
                            </Badge>
                          </div>
                          {task.description && (
                            <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-2">
                              {task.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" /> Created{' '}
                              {new Date(task.created_at).toLocaleDateString()}
                            </span>
                            {task.due_date && (
                              <span className="flex items-center gap-1 text-amber-400">
                                Due {new Date(task.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Completed Tasks & Approvals */}
        {(completedTasks.length > 0 || resolvedApprovals.length > 0) && (
          <div>
            <h2 className="text-base font-semibold mb-4 text-[var(--text-secondary)]">
              Resolved & Completed ({completedTasks.length + resolvedApprovals.length})
            </h2>
            <div className="space-y-2 opacity-75">
              {completedTasks.map((task) => (
                <Card key={task.id} variant="ghost" className="border border-[var(--border-subtle)]">
                  <CardContent className="p-3.5 flex items-center gap-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <p className="text-sm line-through text-[var(--text-secondary)] flex-1">
                      {task.title}
                    </p>
                    <Badge variant="emerald" size="sm">
                      Completed
                    </Badge>
                  </CardContent>
                </Card>
              ))}
              {resolvedApprovals.map((approval) => (
                <Card key={approval.id} variant="ghost" className="border border-[var(--border-subtle)]">
                  <CardContent className="p-3.5 flex items-center gap-3">
                    {approval.status === 'approved' ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-rose-400 flex-shrink-0" />
                    )}
                    <p className="text-sm text-[var(--text-secondary)] flex-1">
                      {approval.title}
                    </p>
                    <Badge
                      variant={approval.status === 'approved' ? 'emerald' : 'rose'}
                      size="sm"
                    >
                      {approval.status}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
