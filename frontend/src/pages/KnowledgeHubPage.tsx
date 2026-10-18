import { useState, useEffect } from 'react'
import {
  Search,
  BookOpen,
  FileText,
  RefreshCw,
  Upload,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  History,
  Send,
  Eye,
  FileSearch,
  Lock,
  Plus,
  Edit3,
  Save,
  FileUp,
  GitCompare,
  Trash2,
} from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/Feedback'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog'
import { GuidelineDiffModal } from '@/components/knowledge/GuidelineDiffModal'
import { knowledgeApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type {
  BrandComplianceReportItem,
  DocumentItem,
  DocumentQueryItem,
  DocumentSummaryItem,
  GuidelineDiffResponse,
  GuidelineItem,
} from '@/types'

export function KnowledgeHubPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  // Tab State
  const [activeTab, setActiveTab] = useState<'personal' | 'official' | 'audit'>('personal')

  // Search & Filter State
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')

  // Data States
  const [personalDocs, setPersonalDocs] = useState<DocumentItem[]>([])
  const [officialGuides, setOfficialGuides] = useState<GuidelineItem[]>([])
  const [loading, setLoading] = useState(true)

  // Dialog States
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadCategory, setUploadCategory] = useState('kt')
  const [uploadTags, setUploadTags] = useState('kt,documentation')
  const [isUploading, setIsUploading] = useState(false)

  // Delete Personal Document State
  const [deleteTargetDoc, setDeleteTargetDoc] = useState<DocumentItem | null>(null)
  const [isDeletingDoc, setIsDeletingDoc] = useState(false)
  const [deleteDocError, setDeleteDocError] = useState<string | null>(null)

  // Create / Upload Official Guideline Dialog (Admin Only)
  const [createGuideOpen, setCreateGuideOpen] = useState(false)
  const [createGuideTitle, setCreateGuideTitle] = useState('')
  const [createGuideCategory, setCreateGuideCategory] = useState('engineering')
  const [createGuideVersion, setCreateGuideVersion] = useState('1.0')
  const [createGuideStatus, setCreateGuideStatus] = useState('published')
  const [createGuideDescription, setCreateGuideDescription] = useState('')
  const [createGuideContent, setCreateGuideContent] = useState('')
  const [createGuideTags, setCreateGuideTags] = useState('official,standard')
  const [createGuideTeams, setCreateGuideTeams] = useState('')
  const [createGuideFile, setCreateGuideFile] = useState<File | null>(null)
  const [isCreatingGuide, setIsCreatingGuide] = useState(false)
  const [createGuideError, setCreateGuideError] = useState<string | null>(null)

  // Edit Official Guideline Dialog (Admin Only)
  const [editGuideOpen, setEditGuideOpen] = useState(false)
  const [editingGuide, setEditingGuide] = useState<GuidelineItem | null>(null)
  const [editGuideTitle, setEditGuideTitle] = useState('')
  const [editGuideCategory, setEditGuideCategory] = useState('engineering')
  const [editGuideVersion, setEditGuideVersion] = useState('1.0')
  const [editGuideStatus, setEditGuideStatus] = useState('published')
  const [editGuideDescription, setEditGuideDescription] = useState('')
  const [editGuideContent, setEditGuideContent] = useState('')
  const [editGuideTags, setEditGuideTags] = useState('')
  const [editGuideTeams, setEditGuideTeams] = useState('')
  const [editGuideChangelog, setEditGuideChangelog] = useState('')
  const [isEditingGuide, setIsEditingGuide] = useState(false)
  const [editGuideError, setEditGuideError] = useState<string | null>(null)

  // Summary Dialog
  const [summaryOpen, setSummaryOpen] = useState(false)
  const [summaryData, setSummaryData] = useState<DocumentSummaryItem | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // Document Query Dialog
  const [queryOpen, setQueryOpen] = useState(false)
  const [activeQueryDoc, setActiveQueryDoc] = useState<DocumentItem | null>(null)
  const [queryInput, setQueryInput] = useState('')
  const [queryResult, setQueryResult] = useState<DocumentQueryItem | null>(null)
  const [queryLoading, setQueryLoading] = useState(false)
  const [queryError, setQueryError] = useState<string | null>(null)

  // Guideline Version History Dialog
  const [versionHistoryOpen, setVersionHistoryOpen] = useState(false)
  const [versionHistory, setVersionHistory] = useState<any[]>([])
  const [selectedGuideTitle, setSelectedGuideTitle] = useState('')

  // View Guideline Content Dialog
  const [viewGuideOpen, setViewGuideOpen] = useState(false)
  const [selectedGuide, setSelectedGuide] = useState<GuidelineItem | null>(null)

  // Semantic Diff State
  const [diffOpen, setDiffOpen] = useState(false)
  const [diffData, setDiffData] = useState<GuidelineDiffResponse | null>(null)
  const [diffLoading, setDiffLoading] = useState(false)
  const [diffError, setDiffError] = useState<string | null>(null)
  const [activeDiffGuide, setActiveDiffGuide] = useState<GuidelineItem | null>(null)

  // Brand Compliance State
  const [auditFilename, setAuditFilename] = useState('hyperrealm_banner.png')
  const [auditFile, setAuditFile] = useState<File | null>(null)
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditReport, setAuditReport] = useState<BrandComplianceReportItem | null>(null)

  // Load Data
  const loadData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'personal') {
        const res = await knowledgeApi.listPersonalDocuments(
          activeCategory === 'all' ? undefined : activeCategory,
          search || undefined
        )
        setPersonalDocs(res.items)
      } else if (activeTab === 'official') {
        const res = await knowledgeApi.listOfficialGuidelines(
          activeCategory === 'all' ? undefined : activeCategory
        )
        setOfficialGuides(res.items)
      }
    } catch (err) {
      console.error('Failed to load knowledge hub data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab !== 'audit') {
      loadData()
    }
  }, [activeTab, activeCategory])

  // Handle Personal Upload
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile || !uploadTitle.trim()) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('title', uploadTitle.trim())
      formData.append('category', uploadCategory)
      formData.append('tags', uploadTags)

      await knowledgeApi.uploadPersonalDocument(formData)
      setUploadOpen(false)
      setUploadFile(null)
      setUploadTitle('')
      loadData()
    } catch (err) {
      console.error('Failed to upload document:', err)
    } finally {
      setIsUploading(false)
    }
  }

  // Handle Delete Personal Document
  const handleConfirmDeleteDoc = async () => {
    if (!deleteTargetDoc) return
    setIsDeletingDoc(true)
    setDeleteDocError(null)
    try {
      await knowledgeApi.deletePersonalDocument(deleteTargetDoc.id)
      setDeleteTargetDoc(null)
      await loadData()
    } catch (err: any) {
      console.error('Failed to delete personal document:', err)
      setDeleteDocError(err?.message || 'Failed to delete personal document.')
    } finally {
      setIsDeletingDoc(false)
    }
  }

  // Handle Document Summary
  const handleOpenSummary = async (doc: DocumentItem) => {
    setSummaryOpen(true)
    setSummaryLoading(true)
    setSummaryData(null)
    setSummaryError(null)
    try {
      const res = await knowledgeApi.getDocumentSummary(doc.id)
      setSummaryData(res)
    } catch (err: any) {
      console.error('Failed to summarize document:', err)
      if (err?.status === 403 || err?.message?.includes('403') || err?.message?.includes('Access denied')) {
        setSummaryError(
          'Access restricted: This personal document belongs to another employee and is isolated by enterprise privacy policies. Only the document author or an administrator can summarize it.'
        )
      } else {
        setSummaryError(err?.message || 'Unable to generate document summary.')
      }
    } finally {
      setSummaryLoading(false)
    }
  }

  // Handle Document Query
  const handleOpenQuery = (doc: DocumentItem) => {
    setActiveQueryDoc(doc)
    setQueryInput('')
    setQueryResult(null)
    setQueryError(null)
    setQueryOpen(true)
  }

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeQueryDoc || !queryInput.trim()) return

    setQueryLoading(true)
    setQueryError(null)
    try {
      const res = await knowledgeApi.queryDocument(activeQueryDoc.id, queryInput.trim())
      setQueryResult(res)
    } catch (err: any) {
      console.error('Failed to query document:', err)
      if (err?.status === 403 || err?.message?.includes('403') || err?.message?.includes('Access denied')) {
        setQueryError(
          'Access restricted: You do not have permission to query this private personal document.'
        )
      } else {
        setQueryError(err?.message || 'Failed to query document.')
      }
    } finally {
      setQueryLoading(false)
    }
  }

  // Handle Version History
  const handleViewVersions = async (guide: GuidelineItem) => {
    setSelectedGuide(guide)
    setSelectedGuideTitle(guide.title)
    setVersionHistoryOpen(true)
    try {
      const versions = await knowledgeApi.listGuidelineVersions(guide.id)
      setVersionHistory(versions)
    } catch (err) {
      console.error('Failed to load guideline versions:', err)
      setVersionHistory([])
    }
  }

  // Handle Semantic Diff
  const handleOpenDiff = async (
    guide: GuidelineItem,
    baseVersion?: string,
    targetVersion?: string
  ) => {
    setActiveDiffGuide(guide)
    setDiffOpen(true)
    setDiffLoading(true)
    setDiffError(null)
    try {
      const res = await knowledgeApi.getGuidelineDiff(guide.id, baseVersion, targetVersion)
      setDiffData(res)
    } catch (err: any) {
      console.error('Failed to load guideline diff:', err)
      setDiffError(err?.message || 'Failed to generate semantic version diff.')
    } finally {
      setDiffLoading(false)
    }
  }

  const handleDiffVersionChange = (baseVersion: string, targetVersion: string) => {
    if (activeDiffGuide) {
      handleOpenDiff(activeDiffGuide, baseVersion, targetVersion)
    }
  }

  // Handle Open Edit Guideline (Admin)
  const handleOpenEditGuide = (guide: GuidelineItem) => {
    setEditingGuide(guide)
    setEditGuideTitle(guide.title)
    setEditGuideCategory(guide.category || 'engineering')
    setEditGuideVersion(guide.version || '1.0')
    setEditGuideStatus(guide.status || 'published')
    setEditGuideDescription(guide.description || '')
    setEditGuideContent(guide.content || '')
    setEditGuideTags((guide.tags || []).join(', '))
    setEditGuideTeams((guide.affected_teams || []).join(', '))
    setEditGuideChangelog('')
    setEditGuideError(null)
    setEditGuideOpen(true)
  }

  // Handle Save Edit Guideline (Admin)
  const handleSaveEditGuide = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingGuide || !editGuideTitle.trim() || !editGuideContent.trim()) return

    setIsEditingGuide(true)
    setEditGuideError(null)
    try {
      const tags = editGuideTags.split(',').map((t) => t.trim()).filter(Boolean)
      const affected_teams = editGuideTeams.split(',').map((t) => t.trim()).filter(Boolean)

      await knowledgeApi.updateOfficialGuideline(editingGuide.id, {
        title: editGuideTitle.trim(),
        category: editGuideCategory,
        version: editGuideVersion.trim() || '1.0',
        status: editGuideStatus,
        description: editGuideDescription.trim(),
        content: editGuideContent,
        tags,
        affected_teams,
        changelog: editGuideChangelog.trim() || undefined,
      })

      const prevVersion = editingGuide.version || '1.0'
      const newVersion = editGuideVersion.trim() || '1.0'
      const targetGuide = { ...editingGuide, version: newVersion, title: editGuideTitle.trim() }

      setEditGuideOpen(false)
      await loadData()

      // Automatically render visual Red/Green diff summary alongside Impact Badges
      handleOpenDiff(targetGuide, prevVersion, newVersion)
    } catch (err: any) {
      console.error('Failed to update guideline:', err)
      setEditGuideError(err?.message || 'Failed to update guideline.')
    } finally {
      setIsEditingGuide(false)
    }
  }

  // Handle Create / Upload Guideline (Admin)
  const handleCreateGuide = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createGuideTitle.trim()) return

    setIsCreatingGuide(true)
    setCreateGuideError(null)
    try {
      if (createGuideFile) {
        const formData = new FormData()
        formData.append('file', createGuideFile)
        formData.append('title', createGuideTitle.trim())
        formData.append('category', createGuideCategory)
        formData.append('version', createGuideVersion.trim() || '1.0')
        formData.append('status_val', createGuideStatus)
        if (createGuideTags.trim()) formData.append('tags', createGuideTags.trim())
        await knowledgeApi.uploadOfficialGuidelineFile(formData)
      } else {
        const tags = createGuideTags.split(',').map((t) => t.trim()).filter(Boolean)
        const affected_teams = createGuideTeams.split(',').map((t) => t.trim()).filter(Boolean)

        await knowledgeApi.createOfficialGuideline({
          title: createGuideTitle.trim(),
          category: createGuideCategory,
          version: createGuideVersion.trim() || '1.0',
          status: createGuideStatus,
          description: createGuideDescription.trim(),
          content: createGuideContent.trim() || 'Official policy and standard guidelines.',
          tags,
          affected_teams,
        })
      }

      setCreateGuideOpen(false)
      setCreateGuideFile(null)
      setCreateGuideTitle('')
      setCreateGuideContent('')
      setCreateGuideDescription('')
      setCreateGuideTags('official,standard')
      setCreateGuideTeams('')
      await loadData()
    } catch (err: any) {
      console.error('Failed to create official guideline:', err)
      setCreateGuideError(err?.message || 'Failed to publish official guideline.')
    } finally {
      setIsCreatingGuide(false)
    }
  }

  // Handle Image Audit
  const handleRunAudit = async (presetFilename?: string) => {
    setAuditLoading(true)
    try {
      let res: BrandComplianceReportItem
      if (auditFile) {
        const formData = new FormData()
        formData.append('file', auditFile)
        res = await knowledgeApi.auditBrandImage(formData)
      } else {
        const targetFilename = presetFilename !== undefined ? presetFilename : auditFilename
        res = await knowledgeApi.auditBrandImage({
          image_filename: targetFilename || undefined,
          image_url: targetFilename ? `https://cdn.hyperrealm.io/assets/${targetFilename}` : undefined,
        })
      }
      setAuditReport(res)
    } catch (err) {
      console.error('Failed to audit brand image:', err)
    } finally {
      setAuditLoading(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5 text-[var(--text-primary)]">
              <BookOpen className="h-6 w-6 text-indigo-400" />
              Governed Knowledge Hub
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Authoritative organizational guidelines, employee KT drive, multimodal vision audits, and Gemini Copilot retrieval.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeTab === 'personal' && (
              <Button onClick={() => setUploadOpen(true)} className="gap-2">
                <Upload className="h-4 w-4" />
                Upload to Personal Hub
              </Button>
            )}
            {activeTab === 'official' && isAdmin && (
              <Button
                onClick={() => {
                  setCreateGuideFile(null)
                  setCreateGuideTitle('')
                  setCreateGuideContent('')
                  setCreateGuideDescription('')
                  setCreateGuideTags('official,standard')
                  setCreateGuideTeams('')
                  setCreateGuideError(null)
                  setCreateGuideOpen(true)
                }}
                className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm"
              >
                <Plus className="h-4 w-4" />
                Upload / Publish Guideline
              </Button>
            )}
            <Button variant="secondary" size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="flex gap-2 p-1 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] w-fit">
          <button
            onClick={() => {
              setActiveTab('personal')
              setActiveCategory('all')
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'personal'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
          >
            <FileText className="h-4 w-4" />
            Personal Hub (My Library)
          </button>
          <button
            onClick={() => {
              setActiveTab('official')
              setActiveCategory('all')
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'official'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Official Guidelines
          </button>
          <button
            onClick={() => {
              setActiveTab('audit')
              setActiveCategory('all')
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'audit'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
          >
            <Sparkles className="h-4 w-4" />
            Brand Compliance Audit
          </button>
        </div>

        {/* ─── TAB 1: PERSONAL KNOWLEDGE HUB ────────────────────────────── */}
        {activeTab === 'personal' && (
          <div className="space-y-5">
            {/* Search & filter */}
            <div className="flex gap-3 flex-wrap">
              <div className="flex-1 min-w-[220px]">
                <Input
                  id="personal-search"
                  placeholder="Search your uploaded KT documents, specs, runbooks…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  leftIcon={<Search className="h-4 w-4" />}
                />
              </div>
            </div>

            {/* Category filter pills */}
            <div className="flex gap-2 flex-wrap">
              {[
                { id: 'all', label: 'All Categories' },
                { id: 'kt', label: 'Knowledge Transfer (KT)' },
                { id: 'architecture', label: 'Architecture & Specs' },
                { id: 'incident', label: 'Incidents & Runbooks' },
                { id: 'engineering', label: 'Engineering' },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${activeCategory === cat.id
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-transparent hover:border-[var(--border-default)]'
                    }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Document list */}
            {personalDocs.length === 0 ? (
              <EmptyState
                icon={<FileText className="h-8 w-8 text-indigo-400" />}
                title="No personal documents uploaded yet"
                description="Upload your private KT documents, architecture notes, or technical specifications to empower your AI Copilot."
                action={
                  <Button onClick={() => setUploadOpen(true)} className="gap-2 mt-2">
                    <Upload className="h-4 w-4" />
                    Upload First Document
                  </Button>
                }
              />
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {personalDocs.map((doc) => (
                  <Card key={doc.id} className="hover:border-indigo-500/40 transition-all flex flex-col justify-between">
                    <CardContent className="p-5 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <div className="h-9 w-9 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                            <FileText className="h-4 w-4 text-indigo-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-sm text-[var(--text-primary)] line-clamp-1">{doc.title}</h3>
                            <span className="text-[11px] text-[var(--text-muted)]">
                              Uploaded {new Date(doc.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 flex-wrap">
                          <Badge variant="indigo" size="sm">
                            Personal
                          </Badge>
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            Indexed
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-[var(--text-secondary)] line-clamp-3 leading-relaxed">
                        {doc.content}
                      </p>

                      <div className="flex items-center gap-2 pt-2 border-t border-[var(--border-subtle)]">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenSummary(doc)}
                          className="text-xs gap-1.5 h-8 flex-1"
                        >
                          <FileSearch className="h-3.5 w-3.5 text-indigo-400" />
                          Summarize
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenQuery(doc)}
                          className="text-xs gap-1.5 h-8 flex-1"
                        >
                          <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                          Ask Document
                        </Button>
                        {(doc.author_id === user?.id || isAdmin) && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setDeleteDocError(null)
                              setDeleteTargetDoc(doc)
                            }}
                            className="text-xs gap-1.5 h-8 text-rose-400 hover:text-white hover:bg-rose-600/30 border-rose-500/20"
                            title="Delete this document"
                          >
                            <Trash2 className="h-3.5 w-3.5 text-rose-400" />
                            Delete
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 2: OFFICIAL GUIDELINES ────────────────────────────────── */}
        {activeTab === 'official' && (
          <div className="space-y-5">
            <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/20 flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-indigo-400 flex-shrink-0" />
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  <span className="font-semibold text-[var(--text-primary)]">Authoritative Knowledge Base:</span>{' '}
                  Accessible to all employees for read-only compliance checks and Q&A.{' '}
                  {isAdmin
                    ? 'As an Administrator, you can upload new guidelines or edit existing organizational policies.'
                    : 'Only administrators can publish or update official policies.'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {isAdmin && (
                  <>
                    <Badge variant="indigo" size="sm">
                      Admin Access Granted
                    </Badge>
                    <Button
                      size="sm"
                      onClick={() => {
                        setCreateGuideFile(null)
                        setCreateGuideTitle('')
                        setCreateGuideContent('')
                        setCreateGuideDescription('')
                        setCreateGuideTags('official,standard')
                        setCreateGuideTeams('')
                        setCreateGuideError(null)
                        setCreateGuideOpen(true)
                      }}
                      className="gap-1.5 text-xs h-8 bg-indigo-600 hover:bg-indigo-500 text-white"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      New Policy
                    </Button>
                  </>
                )}
              </div>
            </div>

            {/* Official category filter pills */}
            <div className="flex gap-2 flex-wrap">
              {[
                { id: 'all', label: 'All Guidelines' },
                { id: 'brand', label: 'Brand & Identity' },
                { id: 'security', label: 'Security & Coding' },
                { id: 'policy', label: 'Policies' },
                { id: 'architecture', label: 'Architecture' },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${activeCategory === cat.id
                      ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-transparent hover:border-[var(--border-default)]'
                    }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Official guidelines list */}
            {officialGuides.length === 0 ? (
              <EmptyState
                icon={<BookOpen className="h-8 w-8 text-indigo-400" />}
                title="No official guidelines published"
                description="Authoritative brand identity, security, and architecture policies will appear here."
              />
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {officialGuides.map((guide) => (
                  <Card key={guide.id} className="hover:border-indigo-500/40 transition-all flex flex-col justify-between">
                    <CardContent className="p-5 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-sm text-[var(--text-primary)]">{guide.title}</h3>
                          <span className="text-[11px] text-[var(--text-muted)]">
                            Effective Date: {guide.effective_date ? new Date(guide.effective_date).toLocaleDateString() : 'Active'}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                            v{guide.version || '1.0'}
                          </span>
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            {guide.status || 'published'}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-[var(--text-secondary)] line-clamp-3 leading-relaxed">
                        {guide.content}
                      </p>

                      <div className="flex items-center gap-2 pt-2 border-t border-[var(--border-subtle)] flex-wrap">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setSelectedGuide(guide)
                            setViewGuideOpen(true)
                          }}
                          className="text-xs gap-1.5 h-8 flex-1"
                        >
                          <Eye className="h-3.5 w-3.5 text-indigo-400" />
                          Read Policy
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleViewVersions(guide)}
                          className="text-xs gap-1.5 h-8 flex-1"
                        >
                          <History className="h-3.5 w-3.5 text-purple-400" />
                          Versions
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenDiff(guide)}
                          className="text-xs gap-1.5 h-8 border-indigo-500/20 text-indigo-300 hover:text-white hover:bg-indigo-600/30 flex-1"
                          title="Compare with previous version and analyze role impacts"
                        >
                          <GitCompare className="h-3.5 w-3.5 text-indigo-400" />
                          Compare Diff
                        </Button>
                        {isAdmin && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleOpenEditGuide(guide)}
                            className="text-xs gap-1.5 h-8 border-indigo-500/30 text-indigo-400 hover:text-white hover:bg-indigo-600/30 hover:border-indigo-400 flex-1"
                            title="Edit this guideline"
                          >
                            <Edit3 className="h-3.5 w-3.5 text-indigo-400" />
                            Edit Policy
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 3: BRAND COMPLIANCE AUDIT ────────────────────────────── */}
        {activeTab === 'audit' && (
          <div className="space-y-6">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <h3 className="font-semibold text-base text-[var(--text-primary)] flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-indigo-400" />
                      Multimodal Vision Brand Compliance Engine
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      Evaluates design assets and presentation slides against Hyperrealm Brand Standards v2.1.
                    </p>
                  </div>
                  <span className="text-[11px] px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                    Target Guideline: Brand Identity Standards v2.1
                  </span>
                </div>

                {/* Preset Scenarios */}
                <div className="space-y-2">
                  <span className="text-xs font-medium text-[var(--text-secondary)]">Test Quick Scenarios:</span>
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setAuditFile(null)
                        setAuditFilename('hyperrealm_banner.png')
                        handleRunAudit('hyperrealm_banner.png')
                      }}
                      className="text-xs"
                    >
                      Banner Asset (Compliant)
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setAuditFile(null)
                        setAuditFilename('bad_violating_slide.png')
                        handleRunAudit('bad_violating_slide.png')
                      }}
                      className="text-xs"
                    >
                      Violating Presentation (Non-Compliant)
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setAuditFile(null)
                        setAuditFilename('')
                        handleRunAudit('')
                      }}
                      className="text-xs"
                    >
                      Empty Asset (Unable to Determine)
                    </Button>
                  </div>
                </div>

                {/* File Upload Selector */}
                <div className="pt-2 flex items-center gap-3">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setAuditFile(e.target.files[0])
                        setAuditFilename(e.target.files[0].name)
                      }
                    }}
                    className="text-xs text-[var(--text-secondary)] file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-indigo-600 file:text-white hover:file:bg-indigo-700"
                  />
                  <Button onClick={() => handleRunAudit()} disabled={auditLoading} className="gap-2">
                    <Sparkles className={`h-4 w-4 ${auditLoading ? 'animate-spin' : ''}`} />
                    {auditLoading ? 'Evaluating Assets…' : 'Run Audit'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Audit Report Display */}
            {auditReport && (
              <Card className="border-indigo-500/30">
                <CardContent className="p-6 space-y-6">
                  {/* Status Banner */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] flex-wrap gap-4">
                    <div className="flex items-center gap-3">
                      {auditReport.status === 'compliant' && <CheckCircle2 className="h-6 w-6 text-emerald-400" />}
                      {auditReport.status === 'non_compliant' && <XCircle className="h-6 w-6 text-rose-400" />}
                      {auditReport.status === 'partially_compliant' && <AlertTriangle className="h-6 w-6 text-amber-400" />}
                      {auditReport.status === 'unable_to_determine' && <HelpCircle className="h-6 w-6 text-slate-400" />}
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-sm text-[var(--text-primary)] capitalize">
                            Overall Status: {auditReport.status.replace(/_/g, ' ')}
                          </h4>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-400">
                            Citing v{auditReport.guideline_version}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5">{auditReport.summary}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-bold px-2 py-1 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                        Mode: {auditReport.analysis_status}
                      </span>
                    </div>
                  </div>

                  {/* Individual Checks */}
                  {(auditReport?.checks ?? []).length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-xs uppercase tracking-wider text-[var(--text-muted)]">
                        Compliance Criteria Breakdown ({(auditReport?.checks ?? []).length})
                      </h4>
                      <div className="grid gap-2">
                        {(auditReport?.checks ?? []).map((chk, idx) => (
                          <div
                            key={idx}
                            className="p-3.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-semibold text-[var(--text-primary)]">{chk.requirement}</span>
                              <span
                                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${chk.result.toLowerCase() === 'passed'
                                    ? 'bg-emerald-500/15 text-emerald-400'
                                    : 'bg-rose-500/15 text-rose-400'
                                  }`}
                              >
                                {chk.result}
                              </span>
                            </div>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                              <span className="font-medium text-[var(--text-muted)]">Observed:</span> {chk.observed_evidence}
                            </p>
                            <span className="text-[10px] text-indigo-400 block">
                              Source: {chk.supporting_source}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {(auditReport?.recommendations ?? []).length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-xs uppercase tracking-wider text-[var(--text-muted)]">
                        Remediation Recommendations
                      </h4>
                      <ul className="list-disc list-inside text-xs text-[var(--text-secondary)] space-y-1">
                        {(auditReport?.recommendations ?? []).map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Limitations */}
                  {(auditReport?.limitations ?? []).length > 0 && (
                    <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-xs text-amber-300 space-y-1">
                      <span className="font-semibold">Review Limitations:</span>
                      <ul className="list-disc list-inside space-y-0.5">
                        {(auditReport?.limitations ?? []).map((lim, i) => (
                          <li key={i}>{lim}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ─── MODAL: Upload Personal Document ────────────────────────────── */}
        <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Upload to Personal Knowledge Hub</DialogTitle>
              <DialogDescription>
                Files uploaded here are stored in your private drive. The AI Copilot can search and cite them.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Document Title *
                </label>
                <Input
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g. Payments Gateway Integration KT"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Category
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)]"
                >
                  <option value="kt">Knowledge Transfer (KT)</option>
                  <option value="architecture">Architecture & Specs</option>
                  <option value="incident">Incident & Runbook</option>
                  <option value="engineering">Engineering Standard</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Tags (comma-separated)
                </label>
                <Input
                  value={uploadTags}
                  onChange={(e) => setUploadTags(e.target.value)}
                  placeholder="payments,checkout,api"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Select File (PDF, DOCX, TXT, PNG, JPEG) *
                </label>
                <input
                  type="file"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadFile(e.target.files[0])
                      if (!uploadTitle) {
                        setUploadTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ''))
                      }
                    }
                  }}
                  className="w-full text-xs text-[var(--text-secondary)]"
                  required
                />
              </div>

              <DialogFooter>
                <Button variant="secondary" type="button" onClick={() => setUploadOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isUploading || !uploadFile} className="gap-2">
                  <Upload className="h-4 w-4" />
                  {isUploading ? 'Uploading…' : 'Upload File'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Delete Personal Document Confirmation ──────────────── */}
        <Dialog open={!!deleteTargetDoc} onOpenChange={(open) => !open && setDeleteTargetDoc(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-rose-400">
                <Trash2 className="h-5 w-5" />
                Delete Personal Document
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to permanently delete{' '}
                <strong className="text-[var(--text-primary)]">"{deleteTargetDoc?.title}"</strong>?
                This file will be removed from your personal hub and Copilot knowledge retrieval.
              </DialogDescription>
            </DialogHeader>

            {deleteDocError && (
              <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs text-red-400">
                {deleteDocError}
              </div>
            )}

            <DialogFooter>
              <Button
                variant="secondary"
                type="button"
                onClick={() => setDeleteTargetDoc(null)}
                disabled={isDeletingDoc}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                type="button"
                onClick={handleConfirmDeleteDoc}
                disabled={isDeletingDoc}
                className="gap-2 bg-rose-600 hover:bg-rose-700 text-white"
              >
                <Trash2 className="h-4 w-4" />
                {isDeletingDoc ? 'Deleting…' : 'Delete Document'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Document Summary ───────────────────────────────────── */}
        <Dialog open={summaryOpen} onOpenChange={setSummaryOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileSearch className="h-5 w-5 text-indigo-400" />
                Document Intelligence Summary
              </DialogTitle>
              <DialogDescription>{summaryData?.title || 'Synthesizing document passages…'}</DialogDescription>
            </DialogHeader>

            {summaryLoading ? (
              <div className="py-8 text-center text-xs text-[var(--text-muted)] animate-pulse">
                Extracting structured content and identifying visual elements…
              </div>
            ) : summaryError ? (
              <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/15 text-xs text-amber-300 space-y-1.5 my-2">
                <div className="flex items-center gap-2 font-semibold">
                  <Lock className="h-4 w-4 text-amber-400" />
                  Access Policy Restricted
                </div>
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{summaryError}</p>
              </div>
            ) : summaryData ? (
              <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
                <div className="p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <h4 className="text-xs font-bold text-[var(--text-primary)] mb-1">Overview</h4>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{summaryData.summary}</p>
                </div>

                {/* Key Points / Highlights / Takeaways */}
                {(summaryData?.key_points ?? summaryData?.key_takeaways ?? summaryData?.highlights ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-[var(--text-primary)] mb-2">Key Highlights</h4>
                    <ul className="list-disc list-inside text-xs text-[var(--text-secondary)] space-y-1">
                      {(summaryData?.key_points ?? summaryData?.key_takeaways ?? summaryData?.highlights ?? []).map((pt, i) => (
                        <li key={i}>{pt}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Visual Elements Detected */}
                {(summaryData?.visual_elements_detected ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-[var(--text-primary)] mb-2">Visual Elements Detected</h4>
                    <div className="flex gap-2 flex-wrap">
                      {(summaryData?.visual_elements_detected ?? []).map((elem, i) => (
                        <span key={i} className="text-[11px] px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          {elem}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citations if present */}
                {(summaryData?.citations ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-[var(--text-primary)] mb-2">Citations</h4>
                    <div className="space-y-1">
                      {(summaryData?.citations ?? []).map((cite, i) => (
                        <div key={i} className="text-[11px] text-[var(--text-muted)] italic p-2 rounded bg-[var(--bg-elevated)]">
                          {cite.title ? `${cite.title}: ` : ''}"{cite.passage}"
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggested Questions */}
                {(summaryData?.suggested_questions ?? []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-[var(--text-primary)] mb-2">Suggested Follow-up Questions</h4>
                    <div className="grid gap-1.5">
                      {(summaryData?.suggested_questions ?? []).map((q, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setSummaryOpen(false)
                            if ((personalDocs ?? []).length > 0) {
                              const doc = (personalDocs ?? []).find((d) => d.id === summaryData.document_id)
                              if (doc) {
                                setActiveQueryDoc(doc)
                                setQueryInput(q)
                                setQueryOpen(true)
                              }
                            }
                          }}
                          className="text-left p-2 rounded bg-[var(--bg-surface)] text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-colors cursor-pointer"
                        >
                          → {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            <DialogFooter>
              <Button onClick={() => setSummaryOpen(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Document Grounded Q&A ──────────────────────────────── */}
        <Dialog open={queryOpen} onOpenChange={setQueryOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-400" />
                Query Document: {activeQueryDoc?.title}
              </DialogTitle>
              <DialogDescription>
                Ask questions strictly grounded in this document's text and extracted visual diagrams.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleRunQuery} className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="e.g. Explain how tokenization is handled..."
                  className="flex-1"
                  required
                />
                <Button type="submit" disabled={queryLoading || !queryInput.trim()} className="gap-1.5">
                  <Send className="h-4 w-4" />
                  Ask
                </Button>
              </div>

              {queryLoading && (
                <div className="py-6 text-center text-xs text-[var(--text-muted)] animate-pulse">
                  Retrieving passages and generating grounded answer…
                </div>
              )}

              {queryError && (
                <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/15 text-xs text-amber-300 space-y-1">
                  <div className="flex items-center gap-2 font-semibold">
                    <Lock className="h-4 w-4 text-amber-400" />
                    Access Policy Restricted
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{queryError}</p>
                </div>
              )}

              {queryResult && (
                <div className="space-y-3 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <h4 className="font-bold text-xs text-[var(--text-primary)]">Grounded Answer:</h4>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{queryResult.answer}</p>

                  {(queryResult?.citations ?? []).length > 0 && (
                    <div className="pt-2 border-t border-[var(--border-subtle)] space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-[var(--text-muted)]">Verified Citations:</span>
                      {(queryResult?.citations ?? []).map((cite, i) => (
                        <div key={i} className="text-[11px] text-[var(--text-muted)] italic p-2 rounded bg-[var(--bg-elevated)]">
                          "{cite.passage}"
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </form>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Guideline Version History ──────────────────────────── */}
        <Dialog open={versionHistoryOpen} onOpenChange={setVersionHistoryOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-indigo-400" />
                Version History: {selectedGuideTitle}
              </DialogTitle>
              <DialogDescription>
                Immutable record of historical revisions, changelogs, and effective dates.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-2 max-h-[50vh] overflow-y-auto">
              {(versionHistory ?? []).length === 0 ? (
                <div className="text-xs text-center py-4 text-[var(--text-muted)]">
                  Only initial revision active.
                </div>
              ) : (
                (versionHistory ?? []).map((v, i) => (
                  <div key={i} className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[var(--text-primary)]">Version {v.version}</span>
                      <span className="text-[10px] uppercase font-bold text-emerald-400">{v.status}</span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)]">{v.changelog}</p>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[10px] text-[var(--text-muted)] block">
                        Recorded: {new Date(v.created_at).toLocaleString()}
                      </span>
                      {selectedGuide && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setVersionHistoryOpen(false)
                            handleOpenDiff(selectedGuide, v.version, selectedGuide.version)
                          }}
                          className="h-6 px-2 text-[11px] gap-1 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 cursor-pointer"
                        >
                          <GitCompare className="h-3 w-3" />
                          Diff vs Active
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <DialogFooter>
              <Button onClick={() => setVersionHistoryOpen(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: View Policy Content ────────────────────────────────── */}
        <Dialog open={viewGuideOpen} onOpenChange={setViewGuideOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedGuide?.title}</DialogTitle>
              <DialogDescription>
                Version {selectedGuide?.version || '1.0'} • Category: {selectedGuide?.category}
              </DialogDescription>
            </DialogHeader>

            <div className="max-h-[60vh] overflow-y-auto p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {selectedGuide?.content}
            </div>

            <DialogFooter>
              <Button onClick={() => setViewGuideOpen(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Upload / Publish Official Guideline (Admin Only) ─────── */}
        <Dialog open={createGuideOpen} onOpenChange={setCreateGuideOpen}>
          <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileUp className="h-5 w-5 text-indigo-400" />
                Upload / Publish Official Guideline
              </DialogTitle>
              <DialogDescription>
                Admin controls: Publish verified organization standards, SOPs, or upload policy documents.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleCreateGuide} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Guideline Title *
                </label>
                <Input
                  value={createGuideTitle}
                  onChange={(e) => setCreateGuideTitle(e.target.value)}
                  placeholder="e.g. Incident Response & Escalation Protocol"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Category
                  </label>
                  <select
                    value={createGuideCategory}
                    onChange={(e) => setCreateGuideCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)]"
                  >
                    <option value="engineering">Engineering</option>
                    <option value="security">Security & Compliance</option>
                    <option value="architecture">Architecture</option>
                    <option value="incident">Incident Response</option>
                    <option value="hr">People & HR</option>
                    <option value="operations">Operations</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Version
                  </label>
                  <Input
                    value={createGuideVersion}
                    onChange={(e) => setCreateGuideVersion(e.target.value)}
                    placeholder="1.0"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Status
                  </label>
                  <select
                    value={createGuideStatus}
                    onChange={(e) => setCreateGuideStatus(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)]"
                  >
                    <option value="published">Published</option>
                    <option value="under_review">Under Review</option>
                    <option value="draft">Draft</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Short Description
                </label>
                <Input
                  value={createGuideDescription}
                  onChange={(e) => setCreateGuideDescription(e.target.value)}
                  placeholder="Executive summary of this policy or guideline..."
                />
              </div>

              <div className="p-3.5 rounded-lg border border-dashed border-[var(--border-default)] bg-[var(--bg-surface)] space-y-2">
                <label className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                  <Upload className="h-4 w-4 text-indigo-400" />
                  Attach Document (PDF, Markdown, TXT)
                </label>
                <input
                  type="file"
                  accept=".pdf,.md,.txt"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const file = e.target.files[0]
                      setCreateGuideFile(file)
                      if (!createGuideTitle) {
                        setCreateGuideTitle(file.name.replace(/\.[^/.]+$/, ''))
                      }
                    }
                  }}
                  className="w-full text-xs text-[var(--text-secondary)]"
                />
                <p className="text-[11px] text-[var(--text-muted)]">
                  If a file is selected, its text will be extracted and published automatically.
                </p>
              </div>

              {!createGuideFile && (
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Policy Content (Markdown or Text)
                  </label>
                  <textarea
                    rows={6}
                    value={createGuideContent}
                    onChange={(e) => setCreateGuideContent(e.target.value)}
                    placeholder="## Purpose&#10;This policy outlines standard practices...&#10;&#10;## Requirements&#10;1. All code commits must undergo peer review..."
                    className="w-full p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)] font-mono resize-y"
                  />
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Tags (comma-separated)
                  </label>
                  <Input
                    value={createGuideTags}
                    onChange={(e) => setCreateGuideTags(e.target.value)}
                    placeholder="security,soc2,sla"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Affected Teams (comma-separated)
                  </label>
                  <Input
                    value={createGuideTeams}
                    onChange={(e) => setCreateGuideTeams(e.target.value)}
                    placeholder="Engineering, DevOps, IT"
                  />
                </div>
              </div>

              {createGuideError && (
                <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs text-red-400">
                  {createGuideError}
                </div>
              )}

              <DialogFooter>
                <Button variant="secondary" type="button" onClick={() => setCreateGuideOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreatingGuide || !createGuideTitle.trim()} className="gap-2">
                  <Plus className="h-4 w-4" />
                  {isCreatingGuide ? 'Publishing…' : 'Publish Guideline'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Edit Existing Guideline (Admin Only) ────────────────── */}
        <Dialog open={editGuideOpen} onOpenChange={setEditGuideOpen}>
          <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5 text-indigo-400" />
                Edit Official Guideline & Policy
              </DialogTitle>
              <DialogDescription>
                Admin controls: Modify specifications, increment revision versions, and append changelog notes.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSaveEditGuide} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Guideline Title *
                </label>
                <Input
                  value={editGuideTitle}
                  onChange={(e) => setEditGuideTitle(e.target.value)}
                  placeholder="Guideline Title"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Category
                  </label>
                  <select
                    value={editGuideCategory}
                    onChange={(e) => setEditGuideCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)]"
                  >
                    <option value="engineering">Engineering</option>
                    <option value="security">Security & Compliance</option>
                    <option value="architecture">Architecture</option>
                    <option value="incident">Incident Response</option>
                    <option value="hr">People & HR</option>
                    <option value="operations">Operations</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Version
                  </label>
                  <Input
                    value={editGuideVersion}
                    onChange={(e) => setEditGuideVersion(e.target.value)}
                    placeholder="e.g. 1.1 or 2.0"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Status
                  </label>
                  <select
                    value={editGuideStatus}
                    onChange={(e) => setEditGuideStatus(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)]"
                  >
                    <option value="published">Published</option>
                    <option value="under_review">Under Review</option>
                    <option value="draft">Draft</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Changelog Note (Saved to Version History)
                </label>
                <Input
                  value={editGuideChangelog}
                  onChange={(e) => setEditGuideChangelog(e.target.value)}
                  placeholder="e.g. Updated SLA response times and on-call escalation rules"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Short Description
                </label>
                <Input
                  value={editGuideDescription}
                  onChange={(e) => setEditGuideDescription(e.target.value)}
                  placeholder="Brief summary of policy updates..."
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                  Policy Content (Markdown) *
                </label>
                <textarea
                  rows={8}
                  value={editGuideContent}
                  onChange={(e) => setEditGuideContent(e.target.value)}
                  className="w-full p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs text-[var(--text-primary)] font-mono resize-y"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Tags (comma-separated)
                  </label>
                  <Input
                    value={editGuideTags}
                    onChange={(e) => setEditGuideTags(e.target.value)}
                    placeholder="security,soc2,sla"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                    Affected Teams (comma-separated)
                  </label>
                  <Input
                    value={editGuideTeams}
                    onChange={(e) => setEditGuideTeams(e.target.value)}
                    placeholder="Engineering, DevOps, IT"
                  />
                </div>
              </div>

              {editGuideError && (
                <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs text-red-400">
                  {editGuideError}
                </div>
              )}

              <DialogFooter>
                <Button variant="secondary" type="button" onClick={() => setEditGuideOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isEditingGuide || !editGuideTitle.trim()} className="gap-2">
                  <Save className="h-4 w-4" />
                  {isEditingGuide ? 'Saving Changes…' : 'Save Changes'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* ─── MODAL: Semantic Diff & Impact Analysis ────────────────────── */}
        <GuidelineDiffModal
          open={diffOpen}
          onOpenChange={setDiffOpen}
          diffData={diffData}
          loading={diffLoading}
          error={diffError}
          onVersionChange={handleDiffVersionChange}
        />
      </div>
    </div>
  )
}
