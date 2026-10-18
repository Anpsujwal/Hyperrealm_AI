import { useState, useEffect, useMemo, useRef } from 'react'
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
  ZoomIn,
  ZoomOut,
  LayoutGrid,
  GitFork,
  Compass,
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
  deptFilter: string
}

function TreeNode({
  node,
  depth = 0,
  collapsedSet,
  toggleCollapse,
  onSelectUser,
  searchQuery,
  selectedUserId,
  deptFilter,
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

  const matchesDept = useMemo(() => {
    if (deptFilter === 'all') return true
    return user.department_name?.toLowerCase() === deptFilter.toLowerCase()
  }, [user, deptFilter])

  return (
    <div className="flex flex-col items-center">
      {/* Node Card Box */}
      <div
        onClick={() => onSelectUser(user)}
        className={`relative rounded-2xl border p-3.5 w-[236px] text-center transition-all duration-200 cursor-pointer shadow-sm select-none group z-10 ${
          isSelected
            ? 'border-indigo-500 bg-indigo-500/15 shadow-[0_0_20px_rgba(99,102,241,0.3)] ring-2 ring-indigo-500/60'
            : matchesSearch
            ? 'border-amber-400 bg-amber-500/15 shadow-[0_0_16px_rgba(245,158,11,0.3)] ring-2 ring-amber-400'
            : deptFilter !== 'all' && matchesDept
            ? 'border-indigo-500/80 bg-[var(--bg-surface)] shadow-md ring-1 ring-indigo-500/40'
            : deptFilter !== 'all' && !matchesDept
            ? 'border-[var(--border-subtle)] bg-[var(--bg-surface)] opacity-50 hover:opacity-100'
            : 'border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-indigo-500/60 hover:bg-[var(--bg-elevated)] hover:shadow-md'
        }`}
      >
        <Avatar name={user.name} size="md" statusDot="online" className="mx-auto mb-2" />
        <p className="text-xs font-bold text-[var(--text-primary)] leading-tight truncate px-1">
          {user.name}
        </p>
        <p className="text-[11px] text-[var(--text-secondary)] mt-0.5 leading-snug truncate px-1 font-medium">
          {user.job_title || user.role?.replace('_', ' ')}
        </p>

        {/* Badges */}
        <div className="flex items-center justify-center gap-1.5 mt-2 flex-wrap">
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

        {/* Project tags */}
        {user.project_ids && user.project_ids.length > 0 && (
          <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] flex items-center justify-center gap-1 flex-wrap">
            <span className="text-[9px] text-[var(--text-muted)] flex items-center gap-0.5">
              <Layers className="h-2.5 w-2.5 text-cyan-500 dark:text-cyan-400" />
            </span>
            {user.project_ids.slice(0, 2).map((pid) => (
              <span
                key={pid}
                className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20 font-medium"
                title={`Project: ${pid.replace('proj_', '').toUpperCase()}`}
              >
                {pid.replace('proj_', '').toUpperCase()}
              </span>
            ))}
            {user.project_ids.length > 2 && (
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                +{user.project_ids.length - 2}
              </span>
            )}
          </div>
        )}

        {/* Expand / Collapse toggle button */}
        {hasReports && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              toggleCollapse(user.id)
            }}
            className="absolute -bottom-3 left-1/2 -translate-x-1/2 z-20 h-6 px-2.5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[10px] font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-indigo-400 hover:bg-indigo-500/10 flex items-center gap-1 shadow-sm transition-all cursor-pointer"
            title={isCollapsed ? 'Expand direct reports' : 'Collapse direct reports'}
          >
            <Users className="h-2.5 w-2.5 text-indigo-500 dark:text-indigo-400" />
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
        <div className="flex flex-col items-center w-full">
          {/* Vertical stem from parent down to the horizontal crossbar */}
          <div className="w-0.5 h-7 bg-indigo-500/40 dark:bg-indigo-400/40" />

          {/* Row of children */}
          <div className="flex justify-center items-start">
            {reports.map((child, index) => {
              const isFirst = index === 0
              const isLast = index === reports.length - 1
              const isOnly = reports.length === 1

              return (
                <div
                  key={child.user?.id || (child as unknown as User).id}
                  className="relative flex flex-col items-center px-3.5"
                >
                  {/* Horizontal crossbar connector */}
                  {!isOnly && (
                    <div
                      className="absolute top-0 h-0.5 bg-indigo-500/40 dark:bg-indigo-400/40"
                      style={{
                        left: isFirst ? '50%' : '0',
                        right: isLast ? '50%' : '0',
                      }}
                    />
                  )}

                  {/* Vertical line dropping down to this child node */}
                  <div className="w-0.5 h-6 bg-indigo-500/40 dark:bg-indigo-400/40" />

                  {/* The child TreeNode */}
                  <TreeNode
                    node={child}
                    depth={depth + 1}
                    collapsedSet={collapsedSet}
                    toggleCollapse={toggleCollapse}
                    onSelectUser={onSelectUser}
                    searchQuery={searchQuery}
                    selectedUserId={selectedUserId}
                    deptFilter={deptFilter}
                  />
                </div>
              )
            })}
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
  const [selectedDept, setSelectedDept] = useState<string>('all')
  const [collapsedSet, setCollapsedSet] = useState<Set<string>>(new Set())
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [zoom, setZoom] = useState(1)
  const [viewMode, setViewMode] = useState<'tree' | 'grid'>('tree')

  // Pan interaction state
  const canvasRef = useRef<HTMLDivElement>(null)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })

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

  // Auto-expand all nodes when searching so matched nodes are immediately visible
  useEffect(() => {
    if (searchQuery.trim()) {
      setCollapsedSet(new Set())
    }
  }, [searchQuery])

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

  // Fit to screen calculation
  const handleFitToScreen = () => {
    if (!canvasRef.current) return
    const container = canvasRef.current
    const content = container.firstElementChild as HTMLElement
    if (!content) return

    const containerWidth = container.clientWidth - 64
    const contentWidth = content.scrollWidth

    if (contentWidth > containerWidth && containerWidth > 0) {
      const fitScale = Math.max(0.6, Number((containerWidth / contentWidth).toFixed(2)))
      setZoom(fitScale)
    } else {
      setZoom(1)
    }

    // Center scroll position
    container.scrollTo({
      left: Math.max(0, (content.scrollWidth - container.clientWidth) / 2),
      top: 0,
      behavior: 'smooth',
    })
  }

  // Mouse pan handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only drag when clicking canvas background, not on interactive cards or buttons
    if ((e.target as HTMLElement).closest('button, input, select, .group')) return
    if (!canvasRef.current) return

    setIsPanning(true)
    setPanStart({
      x: e.clientX,
      y: e.clientY,
      scrollLeft: canvasRef.current.scrollLeft,
      scrollTop: canvasRef.current.scrollTop,
    })
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isPanning || !canvasRef.current) return
    const dx = e.clientX - panStart.x
    const dy = e.clientY - panStart.y
    canvasRef.current.scrollLeft = panStart.scrollLeft - dx
    canvasRef.current.scrollTop = panStart.scrollTop - dy
  }

  const handleMouseUp = () => {
    setIsPanning(false)
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

  // Extract distinct departments from loaded users
  const departmentList = useMemo(() => {
    const depts = new Set<string>()
    allUsers.forEach((u) => {
      if (u.department_name) depts.add(u.department_name)
    })
    return ['all', ...Array.from(depts)]
  }, [allUsers])


  // Filtered users for Grid View
  const filteredGridUsers = useMemo(() => {
    return allUsers.filter((u) => {
      if (selectedDept !== 'all' && u.department_name !== selectedDept) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const match =
          u.name.toLowerCase().includes(q) ||
          (u.job_title || '').toLowerCase().includes(q) ||
          (u.department_name || '').toLowerCase().includes(q) ||
          (u.skills || []).some((s) => s.toLowerCase().includes(q))
        if (!match) return false
      }
      return true
    })
  }, [allUsers, selectedDept, searchQuery])

  return (
    <div className="flex-1 flex overflow-hidden bg-[var(--bg-base)]">
      {/* Main Chart Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Controls Header */}
        <div className="p-6 pb-3 space-y-4 border-b border-[var(--border-subtle)] bg-[var(--bg-base)]">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-bold flex items-center gap-2.5 text-[var(--text-primary)]">
                  <Network className="h-6 w-6 text-indigo-500 dark:text-indigo-400" />
                  Organization Hierarchy
                </h1>
                <Badge variant="indigo" size="sm">
                  {allUsers.length} Employees
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-0.5">
                Authoritative reporting structure from backend records. Visual distinction between line management and project collaboration.
              </p>
            </div>

            {/* Actions & controls */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* View Switcher: Tree vs Grid */}
              <div className="flex items-center rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-0.5 shadow-xs">
                <button
                  onClick={() => setViewMode('tree')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    viewMode === 'tree'
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  <GitFork className="h-3.5 w-3.5" />
                  Tree Diagram
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    viewMode === 'grid'
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  Department Grid
                </button>
              </div>

              {/* Tree-only Zoom Controls */}
              {viewMode === 'tree' && (
                <div className="flex items-center rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-0.5 shadow-xs">
                  <button
                    onClick={() => setZoom((z) => Math.max(0.5, Number((z - 0.1).toFixed(1))))}
                    className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
                    title="Zoom Out"
                  >
                    <ZoomOut className="h-3.5 w-3.5" />
                  </button>
                  <span className="px-2 text-xs font-mono font-medium text-[var(--text-muted)] min-w-[42px] text-center">
                    {Math.round(zoom * 100)}%
                  </span>
                  <button
                    onClick={() => setZoom((z) => Math.min(1.5, Number((z + 0.1).toFixed(1))))}
                    className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
                    title="Zoom In"
                  >
                    <ZoomIn className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={handleFitToScreen}
                    className="px-2 py-1 text-[11px] font-medium text-indigo-600 dark:text-indigo-400 hover:bg-[var(--bg-elevated)] rounded-md border-l border-[var(--border-subtle)] transition-colors cursor-pointer flex items-center gap-1"
                    title="Fit hierarchy to layout box"
                  >
                    <Compass className="h-3 w-3" /> Fit
                  </button>
                  <button
                    onClick={() => setZoom(1)}
                    className="px-2 py-1 text-[10px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md border-l border-[var(--border-subtle)] transition-colors cursor-pointer"
                    title="Reset Zoom (100%)"
                  >
                    100%
                  </button>
                </div>
              )}

              {viewMode === 'tree' && (
                <>
                  <Button variant="secondary" size="sm" onClick={expandAll} title="Expand all nodes">
                    <Maximize2 className="h-3.5 w-3.5 mr-1" /> Expand
                  </Button>
                  <Button variant="secondary" size="sm" onClick={collapseAll} title="Collapse all nodes">
                    <Minimize2 className="h-3.5 w-3.5 mr-1" /> Collapse
                  </Button>
                </>
              )}

              <Button variant="secondary" size="sm" onClick={loadData} disabled={loading} title="Reload hierarchy">
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Search and Filters Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[var(--bg-surface)] p-3 rounded-2xl border border-[var(--border-default)] shadow-xs">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by employee, title, department, or skill (e.g. Ayesha, Pytest)..."
                className="pl-9 bg-[var(--bg-base)] border-[var(--border-subtle)] text-xs h-9 text-[var(--text-primary)]"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {/* Department tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
              {departmentList.map((dept) => (
                <button
                  key={dept}
                  onClick={() => setSelectedDept(dept)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    selectedDept === dept
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  {dept === 'all' ? 'All Departments' : dept}
                </button>
              ))}
            </div>

            {/* Legend */}
            <div className="hidden xl:flex items-center gap-4 text-[11px] text-[var(--text-muted)] border-l border-[var(--border-default)] pl-4">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-indigo-500" />
                Line Management
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded bg-cyan-400" />
                Cross-Project Squad
              </span>
            </div>
          </div>
        </div>

        {/* ─── VIEW 1: SCROLLABLE TREE CANVAS ──────────────────────────── */}
        {viewMode === 'tree' && (
          <div
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className={`flex-1 overflow-auto p-8 relative bg-[var(--bg-base)] ${
              isPanning ? 'cursor-grabbing' : 'cursor-grab'
            }`}
          >
            <div
              className="min-w-fit w-full flex justify-center items-start pb-28 origin-top transition-transform duration-100"
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top center',
              }}
            >
              {loading ? (
                <div className="flex flex-col items-center justify-center p-12 text-sm text-[var(--text-muted)] animate-pulse">
                  <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin mb-3" />
                  Reconstructing organizational hierarchy from backend records...
                </div>
              ) : roots.length === 0 ? (
                <div className="text-center p-12 text-sm text-[var(--text-muted)]">
                  No employees matching filter criteria.
                </div>
              ) : (
                <div className="flex justify-center items-start">
                  {roots.map((rootNode) => (
                    <TreeNode
                      key={rootNode.user?.id || (rootNode as unknown as User).id}
                      node={rootNode}
                      depth={0}
                      collapsedSet={collapsedSet}
                      toggleCollapse={toggleCollapse}
                      onSelectUser={(u) => setSelectedUser(u)}
                      searchQuery={searchQuery}
                      selectedUserId={selectedUser?.id}
                      deptFilter={selectedDept}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── VIEW 2: DEPARTMENT TEAMS GRID MATRIX ────────────────────── */}
        {viewMode === 'grid' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[var(--bg-base)]">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 text-sm text-[var(--text-muted)] animate-pulse">
                <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin mb-3" />
                Loading employee directory...
              </div>
            ) : filteredGridUsers.length === 0 ? (
              <div className="text-center p-12 text-sm text-[var(--text-muted)]">
                No employees matching filter criteria.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredGridUsers.map((user) => {
                  const isSelected = selectedUser?.id === user.id
                  const isManager = allUsers.some((u) => u.manager_id === user.id)
                  const reportsCount = allUsers.filter((u) => u.manager_id === user.id).length

                  return (
                    <div
                      key={user.id}
                      onClick={() => setSelectedUser(user)}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer shadow-xs space-y-3 ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-500/15 ring-2 ring-indigo-500/50 shadow-md'
                          : 'border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-indigo-500/50 hover:bg-[var(--bg-elevated)]'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <Avatar name={user.name} size="md" statusDot="online" />
                        <div className="min-w-0 flex-1">
                          <h4 className="text-sm font-bold text-[var(--text-primary)] truncate">
                            {user.name}
                          </h4>
                          <p className="text-xs text-[var(--text-secondary)] truncate">
                            {user.job_title || user.role?.replace('_', ' ')}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge
                          variant={deptColors[user.department_name ?? ''] ?? 'default'}
                          size="sm"
                          className="text-[10px]"
                        >
                          {user.department_name || 'Engineering'}
                        </Badge>
                        <Badge variant="default" size="sm" className="text-[10px] uppercase">
                          {user.role?.replace('_', ' ')}
                        </Badge>
                      </div>

                      <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                        <div className="flex items-center gap-1 truncate max-w-[150px]">
                          <Mail className="h-3 w-3 flex-shrink-0" />
                          <span className="truncate">{user.email}</span>
                        </div>
                        {isManager && (
                          <span className="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-0.5">
                            <Users className="h-3 w-3" /> {reportsCount}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Slide-over Profile Drawer for Clicked Employee */}
      {selectedUser && (
        <>
          {/* Mobile backdrop */}
          <div
            className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-xs z-30"
            onClick={() => setSelectedUser(null)}
          />
          <div className="fixed inset-y-0 right-0 md:relative md:inset-auto w-full max-w-[370px] flex-shrink-0 border-l border-[var(--border-default)] bg-[var(--bg-surface)] flex flex-col h-full shadow-2xl z-40 md:z-20 animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-4 border-b border-[var(--border-default)] flex items-center justify-between bg-[var(--bg-elevated)]">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-indigo-500 dark:text-indigo-400" />
                <h2 className="text-sm font-semibold text-[var(--text-primary)]">Employee Dossier</h2>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-overlay)] transition-colors cursor-pointer"
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
                <div className="flex items-center justify-center gap-1.5 mt-2 flex-wrap">
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
                  <Network className="h-3.5 w-3.5 text-indigo-500 dark:text-indigo-400" />
                  Reporting Line
                </h4>

                {/* Direct Manager */}
                <div className="p-3 rounded-xl border border-[var(--border-default)] bg-[var(--bg-base)]">
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
                        <p className="text-xs font-semibold text-[var(--text-primary)] truncate hover:text-indigo-500">
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
                      Executive / Board Leadership (Head of Organization)
                    </p>
                  )}
                </div>

                {/* Direct Reports */}
                <div className="p-3 rounded-xl border border-[var(--border-default)] bg-[var(--bg-base)]">
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
                            <p className="text-xs font-semibold text-[var(--text-primary)] truncate hover:text-indigo-500">
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
                  <Layers className="h-3.5 w-3.5 text-cyan-500 dark:text-cyan-400" />
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
                          className="p-3 rounded-xl border border-cyan-500/20 bg-cyan-500/10 space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-cyan-700 dark:text-cyan-300">
                              {proj?.name || pid.replace('proj_', '').toUpperCase()}
                            </span>
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 font-semibold uppercase">
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
                  <div className="p-3 rounded-xl border border-[var(--border-default)] bg-[var(--bg-base)] text-xs text-[var(--text-muted)]">
                    Not currently assigned to external projects.
                  </div>
                )}
              </div>

              {/* Skills & Badges */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                  <Award className="h-3.5 w-3.5 text-amber-500 dark:text-amber-400" />
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
                    <ShieldCheck className="h-3.5 w-3.5 text-indigo-500 dark:text-indigo-400" />
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
                  <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-base)] text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                    Verifying permissions & retrieving confidential records...
                  </div>
                ) : sensitiveDetails ? (
                  <div className="p-3.5 rounded-xl border border-indigo-500/20 bg-indigo-500/10 space-y-2.5 text-xs">
                    <div className="grid grid-cols-2 gap-2 pb-2 border-b border-indigo-500/10">
                      <div>
                        <span className="text-[10px] text-[var(--text-muted)] block">Employee Code</span>
                        <span className="font-mono font-semibold text-[var(--text-primary)]">
                          {sensitiveDetails.employee_code}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-[var(--text-muted)] block">Security Clearance</span>
                        <span className="font-medium text-emerald-600 dark:text-emerald-400">
                          {sensitiveDetails.clearance_level}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pb-2 border-b border-indigo-500/10">
                      <div>
                        <span className="text-[10px] text-[var(--text-muted)] block">Performance Rating</span>
                        <span className="font-medium text-amber-700 dark:text-amber-300">
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
                        <span className="font-semibold text-indigo-700 dark:text-indigo-300">
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
                  <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-amber-700 dark:text-amber-400 text-xs font-semibold">
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
        </>
      )}
    </div>
  )
}
