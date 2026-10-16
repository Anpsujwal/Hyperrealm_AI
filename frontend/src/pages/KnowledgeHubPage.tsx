import { useState, useEffect } from 'react'
import { Search, BookOpen, FileText, RefreshCw } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/Feedback'
import { Button } from '@/components/ui/Button'
import { knowledgeApi } from '@/lib/api'
import type { DocumentItem } from '@/types'

const categories = [
  { id: 'all', label: 'All' },
  { id: 'engineering', label: 'Engineering' },
  { id: 'security', label: 'Security' },
  { id: 'policy', label: 'Policies' },
  { id: 'hr', label: 'HR & People' },
]

export function KnowledgeHubPage() {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')
  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(true)

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const res = await knowledgeApi.listDocuments(
        activeCategory === 'all' ? undefined : activeCategory
      )
      setDocs(res.items)
    } catch (err) {
      console.error('Failed to load documents:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [activeCategory])

  const filtered = docs.filter((d) => {
    const matchesSearch =
      !search ||
      d.title.toLowerCase().includes(search.toLowerCase()) ||
      d.content.toLowerCase().includes(search.toLowerCase())
    return matchesSearch
  })

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5">
              <BookOpen className="h-6 w-6 text-[var(--accent-indigo)]" />
              Knowledge Hub
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Organisational documents, policies, and guidelines stored in SQLite.
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={loadDocuments} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Search + filter */}
        <div className="flex gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <Input
              id="knowledge-search"
              placeholder="Search documents…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
        </div>

        {/* Category tabs */}
        <div className="flex gap-2 flex-wrap">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                activeCategory === cat.id
                  ? 'bg-indigo-500/15 text-[var(--accent-indigo)] border border-indigo-500/30'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-transparent hover:border-[var(--border-default)]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Document grid */}
        {filtered.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="h-7 w-7" />}
            title="No documents found"
            description="Try adjusting your search or category filter."
          />
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {filtered.map((doc) => (
              <Card key={doc.id} interactive className="group hover:border-indigo-500/40 transition-all">
                <CardContent className="p-5">
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 flex-shrink-0 rounded-[var(--radius-md)] flex items-center justify-center bg-indigo-500/10">
                      <FileText className="h-5 w-5 text-indigo-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="font-semibold text-sm text-[var(--text-primary)] group-hover:text-indigo-300 transition-colors">
                          {doc.title}
                        </h3>
                        <Badge variant="indigo" size="sm">
                          {doc.category}
                        </Badge>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed mb-3">
                        {doc.content}
                      </p>
                      <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                        <span>Created {new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
