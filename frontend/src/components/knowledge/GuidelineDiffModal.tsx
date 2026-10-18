import { useState } from 'react'
import {
  GitCompare,
  Layers,
  Users,
  AlertTriangle,
  ShieldCheck,
  Split,
  AlignJustify,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import type { GuidelineDiffResponse } from '@/types'

interface GuidelineDiffModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  diffData: GuidelineDiffResponse | null
  loading?: boolean
  error?: string | null
  onVersionChange?: (baseVersion: string, targetVersion: string) => void
}

export function GuidelineDiffModal({
  open,
  onOpenChange,
  diffData,
  loading,
  error,
  onVersionChange,
}: GuidelineDiffModalProps) {
  const [viewMode, setViewMode] = useState<'sideBySide' | 'unified'>('sideBySide')

  if (!open) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[92vh] flex flex-col p-6 overflow-hidden">
        {/* ─── Header ──────────────────────────────────────────────────────── */}
        <DialogHeader className="pb-3 border-b border-[var(--border-subtle)] flex-shrink-0">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <DialogTitle className="flex items-center gap-2 text-lg font-bold text-[var(--text-primary)]">
                <GitCompare className="h-5 w-5 text-indigo-400" />
                Semantic Version Diff: {diffData?.guideline_title || 'Policy Comparison'}
              </DialogTitle>
              <DialogDescription className="text-xs text-[var(--text-secondary)] mt-0.5">
                Side-by-side policy clause comparison, semantic changelog, and automated role impact analysis.
              </DialogDescription>
            </div>

            {/* View Mode Toggle & Stats */}
            {diffData && (
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <div className="flex items-center rounded-lg border border-[var(--border-default)] p-0.5 bg-[var(--bg-surface)] text-xs">
                  <button
                    type="button"
                    onClick={() => setViewMode('sideBySide')}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-colors ${
                      viewMode === 'sideBySide'
                        ? 'bg-indigo-600 text-white font-medium shadow-xs'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <Split className="h-3.5 w-3.5" />
                    Side-by-Side
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('unified')}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition-colors ${
                      viewMode === 'unified'
                        ? 'bg-indigo-600 text-white font-medium shadow-xs'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <AlignJustify className="h-3.5 w-3.5" />
                    Unified
                  </button>
                </div>

                <div className="flex items-center gap-1.5 text-xs font-mono">
                  <span className="px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
                    +{diffData.stats.additions}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-red-950/40 text-red-400 border border-red-500/30">
                    -{diffData.stats.deletions}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Version Selector Bar */}
          {diffData && diffData.available_versions.length > 1 && (
            <div className="mt-3 flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs">
              <span className="text-[var(--text-muted)] font-medium">Compare:</span>
              <select
                value={diffData.base_version}
                onChange={(e) => onVersionChange?.(e.target.value, diffData.target_version)}
                className="px-2 py-1 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] font-semibold"
              >
                {diffData.available_versions.map((v) => (
                  <option key={v} value={v}>
                    v{v} {v === diffData.base_version ? '(Previous)' : ''}
                  </option>
                ))}
              </select>
              <ArrowRight className="h-3.5 w-3.5 text-[var(--text-muted)]" />
              <select
                value={diffData.target_version}
                onChange={(e) => onVersionChange?.(diffData.base_version, e.target.value)}
                className="px-2 py-1 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] font-semibold text-emerald-400"
              >
                {diffData.available_versions.map((v) => (
                  <option key={v} value={v}>
                    v{v} {v === diffData.target_version ? '(Target/Active)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
        </DialogHeader>

        {/* ─── Scrollable Body ────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
          {loading ? (
            <div className="py-16 text-center text-xs text-[var(--text-muted)] animate-pulse space-y-2">
              <Sparkles className="h-6 w-6 text-indigo-400 mx-auto animate-spin" />
              <div>Computing semantic diff, extracting clause revisions, and scanning role impacts…</div>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl border border-red-500/30 bg-red-950/20 text-xs text-red-400 space-y-1">
              <div className="font-semibold flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Diff Calculation Error
              </div>
              <p>{error}</p>
            </div>
          ) : diffData ? (
            <>
              {/* ─── Top Semantic Impact Card ──────────────────────────────── */}
              <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3.5">
                {/* Impact Header Badge */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-muted)]">
                      Systemic Impact Analysis
                    </span>
                    {diffData.severity === 'high' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        <AlertTriangle className="h-3 w-3 text-amber-400" />
                        High Impact Policy Update
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                        <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                        Standard Revision
                      </span>
                    )}
                  </div>

                  <span className="text-[11px] text-[var(--text-muted)] font-mono">
                    Revision v{diffData.base_version} ➔ v{diffData.target_version}
                  </span>
                </div>

                {/* Impact Badges (e.g. Impacts: Payments Platform) */}
                <div>
                  <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] block mb-1.5">
                    Impact Badges (Affected Systems & Platforms):
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {diffData.impact_badges.map((badge, i) => {
                      const isPayments = badge.toLowerCase().includes('payments')
                      return (
                        <Badge
                          key={i}
                          variant={isPayments ? 'amber' : 'indigo'}
                          className={`text-xs px-2.5 py-1 font-semibold flex items-center gap-1.5 ${
                            isPayments
                              ? 'bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-xs'
                              : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                          }`}
                        >
                          <Layers className={`h-3.5 w-3.5 ${isPayments ? 'text-amber-400' : 'text-indigo-400'}`} />
                          {badge}
                        </Badge>
                      )
                    })}
                  </div>
                </div>

                {/* Affected Roles */}
                {diffData.impacted_roles.length > 0 && (
                  <div>
                    <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] block mb-1.5">
                      Affected Roles & Responsibilities:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {diffData.impacted_roles.map((role, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[11px] font-medium text-[var(--text-secondary)]"
                        >
                          <Users className="h-3 w-3 text-indigo-400" />
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key Semantic Changes List */}
                {diffData.semantic_summary.length > 0 && (
                  <div className="pt-2 border-t border-[var(--border-subtle)] space-y-2">
                    <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] block">
                      Key Policy Modifications:
                    </span>
                    <div className="space-y-1.5">
                      {diffData.semantic_summary.map((item, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 p-2 rounded-lg bg-[var(--bg-elevated)] text-xs border border-[var(--border-subtle)]"
                        >
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              item.change_type === 'breaking'
                                ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                                : item.change_type === 'requirement'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            }`}
                          >
                            {item.change_type}
                          </span>
                          <div className="flex-1">
                            <span className="font-semibold text-[var(--text-primary)] mr-1.5">
                              {item.category}:
                            </span>
                            <span className="text-[var(--text-secondary)] leading-relaxed">
                              {item.description}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* ─── Side-by-Side Semantic Diff Card ──────────────────────── */}
              <div className="rounded-xl border border-[var(--border-subtle)] overflow-hidden bg-[var(--bg-surface)]">
                {/* Card Title Bar */}
                <div className="px-4 py-2.5 bg-[var(--bg-elevated)] border-b border-[var(--border-subtle)] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    <span>Visual Clause Diff Summary</span>
                  </div>
                  <span className="text-[11px] text-[var(--text-muted)]">
                    Red indicates removed/deprecated rules • Green indicates updated/active policy
                  </span>
                </div>

                {viewMode === 'sideBySide' ? (
                  /* ─── Side-by-Side Split View ────────────────────────────── */
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono border-collapse table-fixed">
                      <thead>
                        <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/60 text-[var(--text-muted)] text-[11px]">
                          <th className="w-1/2 p-2 text-left font-semibold border-r border-[var(--border-subtle)]">
                            <span className="text-red-400 font-bold">[-] Previous Revision (v{diffData.base_version})</span>
                          </th>
                          <th className="w-1/2 p-2 text-left font-semibold">
                            <span className="text-emerald-400 font-bold">[+] Active Policy (v{diffData.target_version})</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {diffData.side_by_side.map((row, idx) => {
                          const isOldRemoved = row.old_type === 'removed'
                          const isNewAdded = row.new_type === 'added'

                          return (
                            <tr
                              key={idx}
                              className="border-b border-[var(--border-subtle)]/40 hover:bg-white/[0.02] transition-colors"
                            >
                              {/* Left: Previous Version */}
                              <td
                                className={`p-1.5 align-top border-r border-[var(--border-subtle)] ${
                                  isOldRemoved
                                    ? 'bg-red-950/25 text-red-200 border-l-3 border-l-red-500 font-medium'
                                    : row.old_type === 'empty'
                                    ? 'bg-[var(--bg-elevated)]/25 text-[var(--text-muted)]'
                                    : 'text-[var(--text-secondary)]'
                                }`}
                              >
                                <div className="flex items-start gap-2">
                                  <span className="w-7 text-right select-none text-[10px] text-[var(--text-muted)] flex-shrink-0">
                                    {row.old_line_no || ''}
                                  </span>
                                  <span className="select-none text-red-400/80 w-3 flex-shrink-0">
                                    {isOldRemoved ? '-' : ''}
                                  </span>
                                  <span className="break-words whitespace-pre-wrap flex-1 leading-relaxed">
                                    {row.old_text || ''}
                                  </span>
                                </div>
                              </td>

                              {/* Right: New Target Version */}
                              <td
                                className={`p-1.5 align-top ${
                                  isNewAdded
                                    ? 'bg-emerald-950/25 text-emerald-200 border-l-3 border-l-emerald-500 font-medium'
                                    : row.new_type === 'empty'
                                    ? 'bg-[var(--bg-elevated)]/25 text-[var(--text-muted)]'
                                    : 'text-[var(--text-secondary)]'
                                }`}
                              >
                                <div className="flex items-start gap-2">
                                  <span className="w-7 text-right select-none text-[10px] text-[var(--text-muted)] flex-shrink-0">
                                    {row.new_line_no || ''}
                                  </span>
                                  <span className="select-none text-emerald-400/80 w-3 flex-shrink-0">
                                    {isNewAdded ? '+' : ''}
                                  </span>
                                  <span className="break-words whitespace-pre-wrap flex-1 leading-relaxed">
                                    {row.new_text || ''}
                                  </span>
                                </div>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  /* ─── Unified Inline View ────────────────────────────────── */
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono border-collapse">
                      <tbody>
                        {diffData.unified_diff.map((line, idx) => {
                          const isAdded = line.type === 'added'
                          const isRemoved = line.type === 'removed'

                          return (
                            <tr
                              key={idx}
                              className={`border-b border-[var(--border-subtle)]/30 ${
                                isAdded
                                  ? 'bg-emerald-950/25 text-emerald-200 border-l-3 border-l-emerald-500'
                                  : isRemoved
                                  ? 'bg-red-950/25 text-red-200 border-l-3 border-l-red-500'
                                  : 'text-[var(--text-secondary)] hover:bg-white/[0.02]'
                              }`}
                            >
                              <td className="w-8 p-1.5 text-right select-none text-[10px] text-[var(--text-muted)] border-r border-[var(--border-subtle)]">
                                {line.old_line_no || ''}
                              </td>
                              <td className="w-8 p-1.5 text-right select-none text-[10px] text-[var(--text-muted)] border-r border-[var(--border-subtle)]">
                                {line.new_line_no || ''}
                              </td>
                              <td className="w-4 p-1.5 select-none font-bold text-center">
                                {isAdded ? (
                                  <span className="text-emerald-400">+</span>
                                ) : isRemoved ? (
                                  <span className="text-red-400">-</span>
                                ) : (
                                  ' '
                                )}
                              </td>
                              <td className="p-1.5 break-words whitespace-pre-wrap leading-relaxed">
                                {line.text}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* ─── Footer ──────────────────────────────────────────────────────── */}
        <DialogFooter className="pt-3 border-t border-[var(--border-subtle)] flex-shrink-0 flex items-center justify-between">
          <div className="text-[11px] text-[var(--text-muted)]">
            {diffData && (
              <span>
                Audited & Verified via Hyperrealm Policy Governance Engine
              </span>
            )}
          </div>
          <Button onClick={() => onOpenChange(false)}>Close Diff</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
