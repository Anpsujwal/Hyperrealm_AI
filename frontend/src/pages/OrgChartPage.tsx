import { useState, useEffect, useMemo } from 'react'
import {
  Network,
  RefreshCw,
  Mail,
  Search,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ShieldCheck,
  Users,
  Briefcase,
  Layers,
  Award,
  X,
  Lock,
  Maximize2,
  Minimize2,
} from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { usersApi, adminApi, ApiError } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { OrgNode, User, UserSensitive, ProjectItem } from '@/types'

const deptColors: Record<string, 'indigo' | 'violet' | 'cyan' | 'emerald'> = {
  Engineering: 'indigo',
  Product: 'violet',
  Design: 'cyan',
  Security: 'emerald',
}

interface TreeNodeProps {
  node: OrgNode
  depth?: number
  collapsedSet: Set<string>
  toggleCollapse: (id: string) => void
  onSelectUser: (user: User) => void
  searchQuery: string
  selectedUserId?: string
}

function TreeNode({
  node,
  depth = 0,
  collapsedSet,
  toggleCollapse,
  onSelectUser,
  searchQuery,
  selectedUserId,
}: TreeNodeProps) {
  const user = node.user || (node as unknown as User)
  const reports = node.reports || node.direct_reports || []
  const hasReports = reports.length > 0
  const isCollapsed = collapsedSet.has(user.id)
  const isSelected = selectedUserId === user.id

  const matchesSearch = useMemo(() => {
    if (!searchQuery.trim()) return false
    const q = searchQuery.toLowerCase()
    return (
      user.name.toLowerCase().includes(q) ||
      (user.job_title || '').toLowerCase().includes(q) ||
      (user.department_name || '').toLowerCase().includes(q) ||
      (user.skills || []).some((s) => s.toLowerCase().includes(q))
    )
  }, [user, searchQuery])

  return (
    <div className={`flex flex-col items-center ${depth > 0 ? 'mt-8' : ''}`}>
      {/* Node Card */}
      <div
        onClick={() => onSelectUser(user)}
        className={`relative rounded-xl border p-4 w-[240px] text-center transition-all duration-200 cursor-pointer shadow-md select-none group ${
          isSelected
            ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_rgba(99,102,241,0.25)] ring-2 ring-indigo-500/40'
            : matchesSearch
            ? 'border-amber-400/80 bg-amber-500/10 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
            : 'border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-indigo-500/50 hover:bg-[var(--bg-elevated)]'
        }`}
      >
        <Avatar name={user.name} size="md" statusDot="online" className="mx-auto mb-2" />
        <p className="text-xs font-bold text-[var(--text-primary)] leading-tight truncate px-1">
          {user.name}
        </p>
        <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-snug truncate px-1 font-medium">
          {user.job_title || user.role}
        </p>

        <div className="flex items-center justify-center gap-1.5 mt-2">
          <Badge
            variant={deptColors[user.department_name ?? ''] ?? 'default'}
            size="sm"
            className="text-[9px]"
          >
            {user.department_name || 'Engineering'}
          </Badge>
          <Badge variant="default" size="sm" className="text-[9px] uppercase tracking-wider">
            {user.role?.replace('_', ' ')}
          </Badge>
        </div>

        {/* Project collaboration indicators */}
        {user.project_ids && user.project_ids.length > 0 && (
          <div className="mt-2.5 pt-2 border-t border-[var(--border-subtle)] flex items-center justify-center gap-1 flex-wrap">
            <span className="text-[9px] text-[var(--text-muted)] flex items-center gap-0.5">
              <Layers className="h-2.5 w-2.5 text-cyan-400" />
            </span>
            {user.project_ids.map((pid) => (
              <span
                key={pid}
                className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                title={`Collaborator on ${pid.replace('proj_', '').toUpperCase()}`}
              >
                {pid.replace('proj_', '').toUpperCase()}
              </span>
            ))}
          </div>
        )}

        {/* Expand / Collapse toggle button */}
        {hasReports && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              toggleCollapse(user.id)
            }}
            className="absolute -bottom-3 left-1/2 -translate-x-1/2 h-6 px-2 rounded-full bg-[var(--bg-overlay)] border border-[var(--border-strong)] text-[10px] text-[var(--text-secondary)] hover:text-white hover:border-indigo-400 flex items-center gap-1 shadow-sm transition-all"
            title={isCollapsed ? 'Expand reports' : 'Collapse reports'}
          >
            <Users className="h-2.5 w-2.5 text-indigo-400" />
            <span>{reports.length}</span>
            {isCollapsed ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronUp className="h-3 w-3" />
            )}
          </button>
        )}
      </div>

      {/* Children branches */}
      {hasReports && !isCollapsed && (
        <div className="relative mt-3">
          <div className="w-px h-8 bg-[var(--border-default)] mx-auto" />
          {reports.length > 1 && (
            <div
              className="h-px bg-[var(--border-default)] absolute"
              style={{
                top: 0,
                left: `calc(50% - ${(reports.length - 1) * 135}px)`,
                width: `${(reports.length - 1) * 270}px`,
              }}
            />
          )}
          <div className="flex gap-6">
            {reports.map((child) => (
              <TreeNode
                key={child.user?.id || (child as unknown as User).id}
                node={child}
                depth={depth + 1}
                collapsedSet={collapsedSet}
                toggleCollapse={toggleCollapse}
                onSelectUser={onSelectUser}
                searchQuery={searchQuery}
                selectedUserId={selectedUserId}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function OrgChartPage() {
  const { user: currentUser } = useAuth()
  const [roots, setRoots] = useState<OrgNode[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDept, setSelectedDept] = useState<'all' | 'Engineering' | 'Product'>('all')
  const [collapsedSet, setCollapsedSet] = useState<Set<string>>(new Set())
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  // Sensitive details state
  const [sensitiveDetails, setSensitiveDetails] = useState<UserSensitive | null>(null)
  const [sensitiveLoading, setSensitiveLoading] = useState(false)
  const [sensitiveError, setSensitiveError] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [treeData, dirData, projData] = await Promise.allSettled([
        usersApi.getOrgTree(),
        usersApi.getDirectory(),
        adminApi.listProjects(),
      ])

      if (treeData.status === 'fulfilled') {
        const raw = treeData.value
        const nodes = Array.isArray(raw) ? raw : [raw]
        setRoots(nodes)
      }

      if (dirData.status === 'fulfilled') {
        setAllUsers(dirData.value)
      }

      if (projData.status === 'fulfilled') {
        setProjects(projData.value.items || [])
      }
    } catch (err) {
      console.error('Failed to load org chart data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Toggle collapse for node
  const toggleCollapse = (userId: string) => {
    setCollapsedSet((prev) => {
      const next = new Set(prev)
      if (next.has(userId)) {
        next.delete(userId)
      } else {
        next.add(userId)
      }
      return next
    })
  }

  const expandAll = () => {
    setCollapsedSet(new Set())
  }

  const collapseAll = () => {
    const ids = new Set<string>()
    const collect = (nodes: OrgNode[]) => {
      for (const n of nodes) {
        const u = n.user || (n as unknown as User)
        const reps = n.reports || n.direct_reports || []
        if (reps.length > 0) {
          ids.add(u.id)
          collect(reps)
        }
      }
    }
    collect(roots)
    setCollapsedSet(ids)
  }

  // Load sensitive details when a user is selected
  useEffect(() => {
    if (!selectedUser) {
      setSensitiveDetails(null)
      setSensitiveError(null)
      return
    }

    let active = true
    setSensitiveLoading(true)
    setSensitiveError(null)
    setSensitiveDetails(null)

    usersApi
      .getSensitiveDetails(selectedUser.id)
      .then((data) => {
        if (active) setSensitiveDetails(data)
      })
      .catch((err: ApiError | any) => {
        if (active) {
          if (err.status === 403) {
            setSensitiveError(
              'Confidential details restricted. Only line managers, administrators, or the employee themselves can view salary, clearance, and performance metrics.'
            )
          } else {
            setSensitiveError(err.message || 'Unable to retrieve sensitive employee records.')
          }
        }
      })
      .finally(() => {
        if (active) setSensitiveLoading(false)
      })

    return () => {
      active = false
    }
  }, [selectedUser])

  // Find manager and direct reports for selected user
  const managerUser = useMemo(() => {
    if (!selectedUser?.manager_id) return null
    return allUsers.find((u) => u.id === selectedUser.manager_id) || null
  }, [selectedUser, allUsers])

  const directReports = useMemo(() => {
    if (!selectedUser) return []
    return allUsers.filter((u) => u.manager_id === selectedUser.id)
  }, [selectedUser, allUsers])

  // Filter root trees by department if selected
  const displayedRoots = useMemo(() => {
    if (selectedDept === 'all') return roots
    return roots.filter((r) => {
      const u = r.user || (r as unknown as User)
      return u.department_name === selectedDept
    })
  }, [roots, selectedDept])

  return (
    <div className="flex-1 flex overflow-hidden bg-[var(--bg-base)]">
      {/* Main Chart Area */}
      <div className="flex-1 overflow-auto flex flex-col min-w-0">
        <div className="p-6 space-y-6 min-w-[960px]">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
                <Network className="h-6 w-6 text-[var(--accent-indigo)]" />
                Organization Hierarchy
              </h1>
              <p className="text-sm text-[var(--text-secondary)]">
                Live reporting structure constructed from authoritative backend records. Clear distinction between line management and project collaboration.
              </p>
            </div>

            {/* Actions & controls */}
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={expandAll} title="Expand all nodes">
                <Maximize2 className="h-3.5 w-3.5 mr-1" /> Expand All
              </Button>
              <Button variant="secondary" size="sm" onClick={collapseAll} title="Collapse all nodes">
                <Minimize2 className="h-3.5 w-3.5 mr-1" /> Collapse All
              </Button>
              <Button variant="secondary" size="sm" onClick={loadData} disabled={loading}>
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Search and Filters Bar */}
          <div className="flex items-center justify-between gap-4 bg-[var(--bg-surface)] p-3 rounded-xl border border-[var(--border-default)]">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by employee, title, department, or skill (e.g. Ayesha, Pytest)..."
                className="pl-9 bg-[var(--bg-base)] border-[var(--border-subtle)] text-xs h-9"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)] hover:text-white"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {/* Department tabs */}
            <div className="flex items-center gap-1.5">
              {(['all', 'Engineering', 'Product'] as const).map((dept) => (
                <button
                  key={dept}
                  onClick={() => setSelectedDept(dept)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedDept === dept
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  {dept === 'all' ? 'All Departments' : dept}
                </button>
              ))}
            </div>

            {/* Legend */}
            <div className="hidden lg:flex items-center gap-4 text-[11px] text-[var(--text-muted)] border-l border-[var(--border-default)] pl-4">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-indigo-500" />
                Reporting Line
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded bg-cyan-400" />
                Project Squad
              </span>
            </div>
          </div>

          {/* Hierarchy Chart Tree */}
          <div className="flex justify-center pb-16 pt-4 min-h-[500px]">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 text-sm text-[var(--text-muted)] animate-pulse">
                <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin mb-3" />
                Reconstructing organizational hierarchy from SQLite database...
              </div>
            ) : displayedRoots.length === 0 ? (
              <div className="text-center p-12 text-sm text-[var(--text-muted)]">
                No employees matching filter criteria.
              </div>
            ) : (
              <div className="flex gap-16 justify-center">
                {displayedRoots.map((rootNode) => (
                  <TreeNode
                    key={rootNode.user?.id || (rootNode as unknown as User).id}
                    node={rootNode}
                    depth={0}
                    collapsedSet={collapsedSet}
                    toggleCollapse={toggleCollapse}
                    onSelectUser={(u) => setSelectedUser(u)}
                    searchQuery={searchQuery}
                    selectedUserId={selectedUser?.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Slide-over Profile Drawer for Clicked Employee */}
      {selectedUser && (
        <div className="w-[380px] flex-shrink-0 border-l border-[var(--border-default)] bg-[var(--bg-surface)] flex flex-col h-full shadow-2xl z-30 animate-in slide-in-from-right duration-200">
          {/* Drawer Header */}
          <div className="p-4 border-b border-[var(--border-default)] flex items-center justify-between bg-[var(--bg-elevated)]">
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-[var(--accent-indigo)]" />
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">Employee Dossier</h2>
            </div>
            <button
              onClick={() => setSelectedUser(null)}
              className="p-1 rounded-md text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-overlay)] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Drawer Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {/* Identity Banner */}
            <div className="text-center pb-4 border-b border-[var(--border-subtle)]">
              <Avatar name={selectedUser.name} size="lg" statusDot="online" className="mx-auto mb-3" />
              <h3 className="text-base font-bold text-[var(--text-primary)]">{selectedUser.name}</h3>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-medium">
                {selectedUser.job_title || selectedUser.role}
              </p>
              <div className="flex items-center justify-center gap-1.5 mt-2">
                <Badge variant={deptColors[selectedUser.department_name ?? ''] ?? 'default'} size="sm">
                  {selectedUser.department_name || 'Engineering'}
                </Badge>
                <Badge variant="indigo" size="sm">
                  {selectedUser.role.toUpperCase()}
                </Badge>
                {currentUser?.id === selectedUser.id && (
                  <Badge variant="cyan" size="sm">
                    You
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mt-3">
                <Mail className="h-3.5 w-3.5" />
                <span className="font-mono text-[11px]">{selectedUser.email}</span>
              </div>
            </div>

            {/* Reporting Relationships */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                <Network className="h-3.5 w-3.5 text-indigo-400" />
                Reporting Line
              </h4>

              {/* Direct Manager */}
              <div className="p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-1">
                  Reports To (Direct Manager)
                </span>
                {managerUser ? (
                  <div
                    onClick={() => setSelectedUser(managerUser)}
                    className="flex items-center gap-2.5 cursor-pointer hover:bg-[var(--bg-elevated)] p-1 rounded-md transition-colors"
                  >
                    <Avatar name={managerUser.name} size="sm" />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-[var(--text-primary)] truncate hover:text-indigo-400">
                        {managerUser.name}
                      </p>
                      <p className="text-[10px] text-[var(--text-muted)] truncate">
                        {managerUser.job_title || managerUser.role}
                      </p>
                    </div>
                    <ChevronRight className="h-3.5 w-3.5 text-[var(--text-muted)] ml-auto" />
                  </div>
                ) : (
                  <p className="text-xs text-[var(--text-secondary)] italic">
                    Department Head / Executive (No line manager)
                  </p>
                )}
              </div>

              {/* Direct Reports */}
              <div className="p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-1.5">
                  Direct Reports ({directReports.length})
                </span>
                {directReports.length > 0 ? (
                  <div className="space-y-1.5">
                    {directReports.map((report) => (
                      <div
                        key={report.id}
                        onClick={() => setSelectedUser(report)}
                        className="flex items-center gap-2 cursor-pointer hover:bg-[var(--bg-elevated)] p-1.5 rounded-md transition-colors"
                      >
                        <Avatar name={report.name} size="sm" />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-[var(--text-primary)] truncate hover:text-indigo-400">
                            {report.name}
                          </p>
                          <p className="text-[10px] text-[var(--text-muted)] truncate">
                            {report.job_title || report.role}
                          </p>
                        </div>
                        <ChevronRight className="h-3 w-3 text-[var(--text-muted)]" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[var(--text-muted)] italic">No direct reports.</p>
                )}
              </div>
            </div>

            {/* Project Collaboration vs Reporting Line */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-cyan-400" />
                Cross-Functional Project Squads
              </h4>
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                Project collaboration unites cross-department colleagues independently from hierarchical line management.
              </p>

              {selectedUser.project_ids && selectedUser.project_ids.length > 0 ? (
                <div className="space-y-2">
                  {selectedUser.project_ids.map((pid) => {
                    const proj = projects.find((p) => p.id === pid)
                    return (
                      <div
                        key={pid}
                        className="p-3 rounded-lg border border-cyan-500/20 bg-cyan-950/10 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-cyan-300">
                            {proj?.name || pid.replace('proj_', '').toUpperCase()}
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold uppercase">
                            {proj?.status || 'Active'}
                          </span>
                        </div>
                        <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2">
                          {proj?.description || 'Active enterprise cross-department initiative.'}
                        </p>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)] text-xs text-[var(--text-muted)]">
                  Not currently assigned to external projects.
                </div>
              )}
            </div>

            {/* Skills & Badges */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                <Award className="h-3.5 w-3.5 text-amber-400" />
                Verified Competencies
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(selectedUser.skills && selectedUser.skills.length > 0
                  ? selectedUser.skills
                  : ['FastAPI', 'System Architecture', 'CI/CD']
                ).map((skill) => (
                  <span
                    key={skill}
                    className="text-xs px-2 py-0.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-secondary)]"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Sensitive Employee Details (Permission Enforced) */}
            <div className="space-y-3 pt-2 border-t border-[var(--border-subtle)]">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                  Confidential HR Record
                </h4>
                {sensitiveDetails ? (
                  <Badge variant="emerald" size="sm" className="text-[9px]">
                    Authorized View
                  </Badge>
                ) : sensitiveError ? (
                  <Badge variant="amber" size="sm" className="text-[9px]">
                    Restricted
                  </Badge>
                ) : null}
              </div>

              {sensitiveLoading ? (
                <div className="p-4 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)] text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                  Verifying permissions & retrieving confidential records...
                </div>
              ) : sensitiveDetails ? (
                <div className="p-3.5 rounded-lg border border-indigo-500/20 bg-indigo-950/15 space-y-2.5 text-xs">
                  <div className="grid grid-cols-2 gap-2 pb-2 border-b border-indigo-500/10">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Employee Code</span>
                      <span className="font-mono font-semibold text-[var(--text-primary)]">
                        {sensitiveDetails.employee_code}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Security Clearance</span>
                      <span className="font-medium text-emerald-400">
                        {sensitiveDetails.clearance_level}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pb-2 border-b border-indigo-500/10">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Performance Rating</span>
                      <span className="font-medium text-amber-300">
                        {sensitiveDetails.performance_rating}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Contract Status</span>
                      <span className="text-[var(--text-secondary)]">
                        {sensitiveDetails.contract_type}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Compensation Band</span>
                      <span className="font-semibold text-indigo-300">
                        {sensitiveDetails.salary_band}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">Emergency Contact</span>
                      <span className="text-[11px] text-[var(--text-secondary)] truncate block">
                        {sensitiveDetails.emergency_contact}
                      </span>
                    </div>
                  </div>
                </div>
              ) : sensitiveError ? (
                <div className="p-3.5 rounded-lg border border-amber-500/30 bg-amber-950/10 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold">
                    <Lock className="h-3.5 w-3.5 flex-shrink-0" />
                    Permission Enforced
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                    {sensitiveError}
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
