import { useState, useEffect } from 'react'
import {
  ShieldCheck,
  FileText,
  BookOpen,
  GraduationCap,
  AlertTriangle,
  Users,
  CheckCircle2,
  RefreshCw,
  Edit2,
  Lock,
  Layers,
  Sliders,
  Clock,
  X,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { adminApi, knowledgeApi, learningApi } from '@/lib/api'
import type {
  AuditItem,
  DocumentItem,
  GuidelineItem,
  LearningItem,
  ProjectItem,
} from '@/types'

type AdminTab = 'documents' | 'guidelines' | 'learning_roles' | 'changes_scope' | 'audit_errors'

const ALL_ROLES = [
  { id: 'qa_engineer', label: 'QA Engineer' },
  { id: 'software_developer', label: 'Software Developer' },
  { id: 'devops_engineer', label: 'DevOps Engineer' },
  { id: 'project_manager', label: 'Project Manager' },
  { id: 'technical_lead', label: 'Technical Lead' },
  { id: 'employee', label: 'All Employees' },
]

export function AdminConsolePage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [activeTab, setActiveTab] = useState<AdminTab>('documents')
  const [loading, setLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  // Data states
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [guidelines, setGuidelines] = useState<GuidelineItem[]>([])
  const [learningResources, setLearningResources] = useState<LearningItem[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditItem[]>([])
  const [ingestionErrors, setIngestionErrors] = useState<AuditItem[]>([])
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [auditFilter, setAuditFilter] = useState<'errors' | 'all'>('errors')

  // Document metadata edit modal
  const [editingDoc, setEditingDoc] = useState<DocumentItem | null>(null)
  const [docCategory, setDocCategory] = useState('')
  const [docIsPublic, setDocIsPublic] = useState(true)

  // Guideline status edit modal
  const [editingGuide, setEditingGuide] = useState<GuidelineItem | null>(null)
  const [guideStatus, setGuideStatus] = useState('published')
  const [guideVersion, setGuideVersion] = useState('')
  const [guideChangelog, setGuideChangelog] = useState('')

  // Learning role requirement edit
  const [editingResource, setEditingResource] = useState<LearningItem | null>(null)
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])
  const [dueDays, setDueDays] = useState(30)

  const loadAdminData = async () => {
    if (!isAdmin) return
    setLoading(true)
    try {
      const [docRes, guideRes, learnRes, auditRes, errRes, projRes] = await Promise.allSettled([
        knowledgeApi.listDocuments(),
        adminApi.listGuidelineChanges(),
        learningApi.listResources(),
        adminApi.listAuditLogs(),
        adminApi.listIngestionErrors(),
        adminApi.listProjects(),
      ])

      if (docRes.status === 'fulfilled') setDocuments(docRes.value.items || [])
      if (guideRes.status === 'fulfilled') setGuidelines(guideRes.value.items || [])
      if (learnRes.status === 'fulfilled') setLearningResources(learnRes.value.items || [])
      if (auditRes.status === 'fulfilled') setAuditLogs(auditRes.value.items || [])
      if (errRes.status === 'fulfilled') setIngestionErrors(errRes.value.items || [])
      if (projRes.status === 'fulfilled') setProjects(projRes.value.items || [])
    } catch (err) {
      console.error('Failed to load admin data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAdminData()
  }, [isAdmin])

  // Save Document Metadata
  const handleSaveDocMetadata = async () => {
    if (!editingDoc) return
    try {
      await adminApi.updateDocumentMetadata(editingDoc.id, {
        category: docCategory,
        is_public: docIsPublic,
      })
      setActionMessage(`Updated metadata for "${editingDoc.title}"`)
      setEditingDoc(null)
      await loadAdminData()
    } catch (err: any) {
      alert(err.message || 'Failed to update document metadata')
    }
  }

  // Save Guideline Status/Version
  const handleSaveGuideline = async () => {
    if (!editingGuide) return
    try {
      await adminApi.updateGuideline(editingGuide.id, {
        status: guideStatus,
        version: guideVersion,
        changelog: guideChangelog,
      })
      setActionMessage(`Updated publication status for "${editingGuide.title}"`)
      setEditingGuide(null)
      await loadAdminData()
    } catch (err: any) {
      alert(err.message || 'Failed to update guideline')
    }
  }

  // Save Learning Requirements
  const handleSaveRequirements = async () => {
    if (!editingResource) return
    try {
      await adminApi.assignLearningRequirements(editingResource.id, {
        required_for_roles: selectedRoles,
        due_days: dueDays,
      })
      setActionMessage(`Assigned role requirements for "${editingResource.title}"`)
      setEditingResource(null)
      await loadAdminData()
    } catch (err: any) {
      alert(err.message || 'Failed to assign requirements')
    }
  }

  // Non-Admin Permission Guard Screen
  if (!isAdmin) {
    return (
      <div className="flex-1 flex items-center justify-center p-6 bg-[var(--bg-base)]">
        <Card className="max-w-md w-full p-8 text-center border-amber-500/30 bg-amber-950/10 shadow-2xl">
          <div className="h-14 w-14 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto mb-4">
            <Lock className="h-7 w-7 text-amber-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Admin Authority Required</h2>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
            Access to the Hyperrealm Admin Console is strictly reserved for administrative accounts.
            Your active role <span className="text-amber-400 font-semibold font-mono">"{user?.role || 'user'}"</span> does not have administrative clearance.
          </p>
          <div className="p-3 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-xs text-[var(--text-muted)] mb-6 text-left space-y-1">
            <p className="font-semibold text-[var(--text-primary)]">Enforced Security Safeguards:</p>
            <p>• Backend endpoints reject with HTTP 403 Forbidden</p>
            <p>• Audit log immutable security ledger</p>
            <p>• Role-based permission dependency verification</p>
          </div>
          <Button variant="primary" onClick={() => window.history.back()} className="w-full">
            Return to Authorized Workspace
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)]">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
              <ShieldCheck className="h-6 w-6 text-[var(--accent-indigo)]" />
              Administrative Governance Console
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Authorized interface for knowledge document metadata, guideline versioning, role-based learning assignments, and audit ingestion diagnostics.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={loadAdminData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Badge variant="indigo" className="font-semibold">
              Admin: {user?.email}
            </Badge>
          </div>
        </div>

        {/* Action feedback toast */}
        {actionMessage && (
          <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between animate-in fade-in">
            <span className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              {actionMessage}
            </span>
            <button
              onClick={() => setActionMessage(null)}
              className="text-emerald-400 hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[var(--border-default)] overflow-x-auto pb-1 scrollbar-hide">
          {[
            { id: 'documents', label: 'Knowledge Documents', icon: BookOpen, count: documents.length },
            { id: 'guidelines', label: 'Guideline Versions & Status', icon: FileText, count: guidelines.length },
            { id: 'learning_roles', label: 'Learning Role Assignments', icon: GraduationCap, count: learningResources.length },
            { id: 'changes_scope', label: 'Guideline Changes & Scope', icon: Layers, count: guidelines.length },
            { id: 'audit_errors', label: 'Audit & Ingestion Errors', icon: AlertTriangle, count: ingestionErrors.length },
          ].map((tab) => {
            const Icon = tab.icon
            const isSelected = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as AdminTab)}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-all border-b-2 flex-shrink-0 cursor-pointer ${
                  isSelected
                    ? 'border-indigo-500 text-[var(--accent-indigo)] bg-indigo-500/10'
                    : 'border-transparent text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-elevated)]'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-[var(--bg-overlay)] text-[var(--text-secondary)]">
                  {tab.count}
                </span>
              </button>
            )
          })}
        </div>

        {/* ─── TAB 1: Knowledge Documents & Metadata ──────────────────────── */}
        {activeTab === 'documents' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white">Knowledge Documents & Metadata</h2>
                <p className="text-xs text-[var(--text-secondary)]">
                  Configure categories, access visibility, and metadata schemas across organizational documents.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {documents.map((doc) => (
                <Card key={doc.id} className="p-4 border-[var(--border-default)]">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-[var(--text-primary)]">
                          {doc.title}
                        </span>
                        <Badge variant="indigo" size="sm" className="capitalize">
                          {doc.category}
                        </Badge>
                        <Badge variant={doc.is_public !== false ? 'emerald' : 'amber'} size="sm">
                          {doc.is_public !== false ? 'Public / Org-wide' : 'Confidential'}
                        </Badge>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono">
                          v{doc.version || 1}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
                        {doc.content.replace(/[#*`]/g, '')}
                      </p>
                      <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)] pt-1">
                        <span>ID: {doc.id}</span>
                        <span>Author ID: {doc.author_id}</span>
                        <span>Created: {new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      className="text-xs flex items-center gap-1.5 flex-shrink-0"
                      onClick={() => {
                        setEditingDoc(doc)
                        setDocCategory(doc.category)
                        setDocIsPublic(doc.is_public !== false)
                      }}
                    >
                      <Edit2 className="h-3.5 w-3.5" /> Edit Metadata
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ─── TAB 2: Guideline Versions & Publication Status ──────────────── */}
        {activeTab === 'guidelines' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white">Guideline Versions & Publication Status</h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Review semantic version numbers, active publication state, effective and review dates.
              </p>
            </div>

            <div className="space-y-3">
              {guidelines.map((guide) => (
                <Card key={guide.id} className="p-4 border-[var(--border-default)]">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-[var(--text-primary)]">
                          {guide.title}
                        </span>
                        <Badge variant="cyan" size="sm" className="font-mono">
                          v{guide.version || '1.0'}
                        </Badge>
                        <Badge
                          variant={
                            guide.status === 'published'
                              ? 'emerald'
                              : guide.status === 'review'
                              ? 'amber'
                              : 'default'
                          }
                          size="sm"
                          className="capitalize font-semibold"
                        >
                          {guide.status || 'published'}
                        </Badge>
                        <Badge variant="default" size="sm" className="capitalize">
                          {guide.category}
                        </Badge>
                      </div>

                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2">
                        {guide.content}
                      </p>

                      <div className="flex items-center gap-4 text-[10px] text-[var(--text-muted)] pt-1 flex-wrap">
                        <span>Owner ID: {guide.owner_id}</span>
                        {guide.effective_date && (
                          <span>Effective: {new Date(guide.effective_date).toLocaleDateString()}</span>
                        )}
                        {guide.review_date && (
                          <span>Next Review: {new Date(guide.review_date).toLocaleDateString()}</span>
                        )}
                        {guide.changelog && (
                          <span className="text-indigo-400 font-medium">{guide.changelog}</span>
                        )}
                      </div>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      className="text-xs flex items-center gap-1.5 flex-shrink-0"
                      onClick={() => {
                        setEditingGuide(guide)
                        setGuideStatus(guide.status || 'published')
                        setGuideVersion(guide.version || '1.0')
                        setGuideChangelog(guide.changelog || '')
                      }}
                    >
                      <Sliders className="h-3.5 w-3.5" /> Manage Status
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ─── TAB 3: Assigning Learning Requirements by Role ──────────────── */}
        {activeTab === 'learning_roles' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white">Assign Learning Requirements by Role</h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Designate which curriculum items are mandatory for specific engineering and product roles.
              </p>
            </div>

            <div className="space-y-3">
              {learningResources.map((res) => (
                <Card key={res.id} className="p-4 border-[var(--border-default)]">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-[var(--text-primary)]">
                          {res.title}
                        </span>
                        <Badge variant="indigo" size="sm" className="capitalize">
                          {res.category}
                        </Badge>
                        <span className="text-xs text-[var(--text-muted)] flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {res.estimated_minutes} mins
                        </span>
                      </div>

                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                        {res.description}
                      </p>

                      <div className="pt-1">
                        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-1">
                          Mandatory Requirement For Roles:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {res.required_for_roles && res.required_for_roles.length > 0 ? (
                            res.required_for_roles.map((r) => (
                              <Badge key={r} variant="emerald" size="sm" className="text-[10px] uppercase">
                                {r.replace('_', ' ')}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-xs text-[var(--text-muted)] italic">
                              Elective / No mandatory assignment
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      className="text-xs flex items-center gap-1.5 flex-shrink-0"
                      onClick={() => {
                        setEditingResource(res)
                        setSelectedRoles(res.required_for_roles || [])
                        setDueDays(res.due_days || 30)
                      }}
                    >
                      <Users className="h-3.5 w-3.5" /> Assign Roles
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ─── TAB 4: Guideline Changes & Affected Scope ───────────────────── */}
        {activeTab === 'changes_scope' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white">Recent Guideline Changes & Affected Teams/Projects</h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Track guideline modifications and inspect which squad teams and delivery projects are impacted.
              </p>
            </div>

            <div className="space-y-4">
              {guidelines.map((guide) => (
                <Card key={guide.id} className="p-5 border-l-4 border-l-indigo-500">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-sm text-[var(--text-primary)]">
                          {guide.title}
                        </h3>
                        <Badge variant="cyan" size="sm" className="font-mono">
                          v{guide.version || '1.0'}
                        </Badge>
                        <Badge variant="emerald" size="sm">
                          {guide.status || 'published'}
                        </Badge>
                      </div>
                      <p className="text-xs text-indigo-400 font-medium mt-1">
                        Changelog: {guide.changelog || 'Initial version published.'}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
                    {guide.content}
                  </p>

                  <div className="grid sm:grid-cols-2 gap-4 pt-3 border-t border-[var(--border-subtle)] text-xs">
                    {/* Affected Teams */}
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1.5">
                        Affected Departments & Teams
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {(guide.affected_teams && guide.affected_teams.length > 0
                          ? guide.affected_teams
                          : ['Engineering', 'QA']
                        ).map((team) => (
                          <span
                            key={team}
                            className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/20 font-medium"
                          >
                            {team}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Affected Projects */}
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider block mb-1.5">
                        Affected Delivery Projects
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {(guide.affected_projects && guide.affected_projects.length > 0
                          ? guide.affected_projects
                          : ['proj_phoenix']
                        ).map((projId) => {
                          const projName = projects.find((p) => p.id === projId)?.name || projId
                          return (
                            <span
                              key={projId}
                              className="text-[11px] px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/20 font-medium"
                            >
                              {projName}
                            </span>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ─── TAB 5: Audit Events & Ingestion Errors ──────────────────────── */}
        {activeTab === 'audit_errors' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-white">System Audit & Ingestion Error Diagnostics</h2>
                <p className="text-xs text-[var(--text-secondary)]">
                  Immutable audit records, parse failures, schema validation errors, and access control rejections.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={auditFilter === 'errors' ? 'primary' : 'secondary'}
                  size="sm"
                  className="text-xs"
                  onClick={() => setAuditFilter('errors')}
                >
                  Ingestion Errors ({ingestionErrors.length})
                </Button>
                <Button
                  variant={auditFilter === 'all' ? 'primary' : 'secondary'}
                  size="sm"
                  className="text-xs"
                  onClick={() => setAuditFilter('all')}
                >
                  All Audit Logs ({auditLogs.length})
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              {(auditFilter === 'errors' ? ingestionErrors : auditLogs).length === 0 ? (
                <Card className="p-8 text-center text-xs text-[var(--text-muted)]">
                  {auditFilter === 'errors'
                    ? 'No system ingestion errors detected. All documents and schemas verified clean.'
                    : 'No audit records recorded.'}
                </Card>
              ) : (
                (auditFilter === 'errors' ? ingestionErrors : auditLogs).map((record) => {
                  const isError =
                    record.action === 'auth_failure' ||
                    record.action === 'permission_denied' ||
                    record.description.toLowerCase().includes('fail') ||
                    record.description.toLowerCase().includes('error')

                  return (
                    <Card
                      key={record.id}
                      className={`p-4 border ${
                        isError
                          ? 'border-amber-500/40 bg-amber-950/10'
                          : 'border-[var(--border-default)]'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge
                              variant={isError ? 'amber' : 'default'}
                              size="sm"
                              className="uppercase text-[10px] font-bold"
                            >
                              {record.action}
                            </Badge>
                            <span className="text-xs font-semibold text-white">
                              {record.resource_type}
                            </span>
                            {record.actor_email && (
                              <span className="text-[11px] text-indigo-400 font-mono">
                                Actor: {record.actor_email}
                              </span>
                            )}
                            {record.ip_address && (
                              <span className="text-[10px] text-[var(--text-muted)] font-mono">
                                IP: {record.ip_address}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                            {record.description}
                          </p>
                          {record.metadata && Object.keys(record.metadata).length > 0 && (
                            <pre className="text-[10px] text-[var(--text-muted)] font-mono bg-[var(--bg-base)] p-2 rounded border border-[var(--border-subtle)] mt-1.5 overflow-x-auto">
                              {JSON.stringify(record.metadata, null, 2)}
                            </pre>
                          )}
                        </div>
                        <span className="text-[10px] text-[var(--text-muted)] flex-shrink-0">
                          {new Date(record.created_at).toLocaleString()}
                        </span>
                      </div>
                    </Card>
                  )
                })
              )}
            </div>
          </div>
        )}

        {/* ─── MODAL: Document Metadata Editor ────────────────────────────── */}
        {editingDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <Card className="max-w-md w-full p-6 space-y-4 bg-[var(--bg-surface)] border-[var(--border-strong)] shadow-2xl">
              <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
                <h3 className="font-bold text-sm text-white">Edit Document Metadata</h3>
                <button
                  onClick={() => setEditingDoc(null)}
                  className="text-[var(--text-muted)] hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-[var(--text-muted)] block mb-1">Document Title</label>
                  <input
                    disabled
                    value={editingDoc.title}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-[var(--text-muted)] text-xs cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="text-[var(--text-muted)] block mb-1">Category</label>
                  <select
                    value={docCategory}
                    onChange={(e) => setDocCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-white text-xs"
                  >
                    <option value="engineering">Engineering</option>
                    <option value="security">Security</option>
                    <option value="hr">HR & People</option>
                    <option value="process">Process & Agile</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div>
                  <label className="text-[var(--text-muted)] block mb-1">Visibility Scope</label>
                  <div className="flex items-center gap-4 pt-1">
                    <label className="flex items-center gap-1.5 cursor-pointer text-white">
                      <input
                        type="radio"
                        checked={docIsPublic}
                        onChange={() => setDocIsPublic(true)}
                        name="visibility"
                      />
                      Public (All Employees)
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer text-white">
                      <input
                        type="radio"
                        checked={!docIsPublic}
                        onChange={() => setDocIsPublic(false)}
                        name="visibility"
                      />
                      Confidential (Restricted)
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
                <Button variant="secondary" size="sm" onClick={() => setEditingDoc(null)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleSaveDocMetadata}>
                  Save Metadata
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* ─── MODAL: Guideline Status & Version Editor ─────────────────────── */}
        {editingGuide && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <Card className="max-w-md w-full p-6 space-y-4 bg-[var(--bg-surface)] border-[var(--border-strong)] shadow-2xl">
              <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
                <h3 className="font-bold text-sm text-white">Manage Guideline Version & Status</h3>
                <button
                  onClick={() => setEditingGuide(null)}
                  className="text-[var(--text-muted)] hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-[var(--text-muted)] block mb-1">Guideline Title</label>
                  <input
                    disabled
                    value={editingGuide.title}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-[var(--text-muted)] text-xs cursor-not-allowed"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[var(--text-muted)] block mb-1">Version (Semantic)</label>
                    <Input
                      value={guideVersion}
                      onChange={(e) => setGuideVersion(e.target.value)}
                      placeholder="e.g. 2.2"
                      className="text-xs h-9"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-muted)] block mb-1">Publication Status</label>
                    <select
                      value={guideStatus}
                      onChange={(e) => setGuideStatus(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-white text-xs h-9"
                    >
                      <option value="published">Published</option>
                      <option value="review">Under Review</option>
                      <option value="draft">Draft</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[var(--text-muted)] block mb-1">Changelog Summary</label>
                  <Input
                    value={guideChangelog}
                    onChange={(e) => setGuideChangelog(e.target.value)}
                    placeholder="Describe what changed in this version..."
                    className="text-xs h-9"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
                <Button variant="secondary" size="sm" onClick={() => setEditingGuide(null)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleSaveGuideline}>
                  Update Guideline
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* ─── MODAL: Learning Role Assignment Editor ──────────────────────── */}
        {editingResource && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <Card className="max-w-lg w-full p-6 space-y-4 bg-[var(--bg-surface)] border-[var(--border-strong)] shadow-2xl">
              <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
                <h3 className="font-bold text-sm text-white">Assign Role Requirements</h3>
                <button
                  onClick={() => setEditingResource(null)}
                  className="text-[var(--text-muted)] hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[var(--text-muted)] block mb-0.5">Module:</span>
                  <span className="font-bold text-sm text-indigo-300 block">
                    {editingResource.title}
                  </span>
                </div>

                <div>
                  <label className="text-[var(--text-muted)] block mb-2 font-semibold">
                    Designate Mandatory Roles:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {ALL_ROLES.map((r) => {
                      const isChecked = selectedRoles.includes(r.id)
                      return (
                        <label
                          key={r.id}
                          className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                            isChecked
                              ? 'border-indigo-500 bg-indigo-500/15 text-white'
                              : 'border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {
                              setSelectedRoles((prev) =>
                                isChecked ? prev.filter((id) => id !== r.id) : [...prev, r.id]
                              )
                            }}
                            className="rounded"
                          />
                          <span className="font-medium text-xs">{r.label}</span>
                        </label>
                      )
                    })}
                  </div>
                </div>

                <div>
                  <label className="text-[var(--text-muted)] block mb-1">
                    Completion Due Window (Days from onboarding)
                  </label>
                  <Input
                    type="number"
                    value={dueDays}
                    onChange={(e) => setDueDays(parseInt(e.target.value, 10) || 30)}
                    min={1}
                    max={180}
                    className="text-xs h-9 w-32"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[var(--border-subtle)]">
                <Button variant="secondary" size="sm" onClick={() => setEditingResource(null)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleSaveRequirements}>
                  Save Assignments
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
