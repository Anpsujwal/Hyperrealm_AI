import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MarkdownContentProps {
  content: string
  className?: string
}

function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative my-3 rounded-xl overflow-hidden border border-[var(--border-strong)] bg-[var(--bg-elevated)]/90 shadow-sm text-xs font-mono">
      <div className="flex items-center justify-between px-3.5 py-1.5 border-b border-[var(--border-default)] bg-[var(--bg-surface)] text-[var(--text-muted)] text-[11px]">
        <span className="font-semibold uppercase tracking-wider">{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-emerald-400" />
              <span className="text-emerald-400 text-[10px]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span className="text-[10px]">Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-[var(--text-primary)] text-xs leading-relaxed selection:bg-purple-500/30">
        <code>{code}</code>
      </pre>
    </div>
  )
}

function renderFormattedText(text: string) {
  // Format bold, italics, inline code, links
  const parts: (string | React.ReactNode)[] = []
  let keyIndex = 0

  const inlineRegex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|https?:\/\/[^\s]+)/g
  let lastIdx = 0
  let match: RegExpExecArray | null

  while ((match = inlineRegex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index))
    }
    const token = match[0]
    if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={`inline-code-${keyIndex++}`}
          className="px-1.5 py-0.5 mx-0.5 rounded-md bg-[var(--bg-elevated)] text-[var(--accent-indigo)] font-mono text-[12px] border border-[var(--border-subtle)] font-medium"
        >
          {token.slice(1, -1)}
        </code>
      )
    } else if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={`bold-${keyIndex++}`} className="font-semibold text-[var(--text-primary)]">
          {token.slice(2, -2)}
        </strong>
      )
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={`italic-${keyIndex++}`} className="italic text-[var(--text-secondary)]">
          {token.slice(1, -1)}
        </em>
      )
    } else if (token.startsWith('http')) {
      parts.push(
        <a
          key={`link-${keyIndex++}`}
          href={token}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--accent-indigo)] hover:underline inline-flex items-center gap-0.5"
        >
          {token}
        </a>
      )
    }
    lastIdx = inlineRegex.lastIndex
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx))
  }

  return parts.length > 0 ? parts : text
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  if (!content) return null

  const blocks: React.ReactNode[] = []
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  let blockIdx = 0

  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const textBlock = content.substring(lastIndex, match.index)
      blocks.push(
        <div key={`text-${blockIdx++}`} className="space-y-2">
          {renderTextParagraphs(textBlock)}
        </div>
      )
    }
    const lang = match[1] || ''
    const code = match[2].trimEnd()
    blocks.push(<CodeBlock key={`code-${blockIdx++}`} code={code} language={lang} />)
    lastIndex = codeBlockRegex.lastIndex
  }

  if (lastIndex < content.length) {
    const textBlock = content.substring(lastIndex)
    blocks.push(
      <div key={`text-${blockIdx++}`} className="space-y-2">
        {renderTextParagraphs(textBlock)}
      </div>
    )
  }

  return <div className={cn('text-sm leading-relaxed space-y-2', className)}>{blocks}</div>
}

function renderTextParagraphs(text: string) {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let lineIdx = 0
  let listItems: string[] = []
  let isNumbered = false

  const flushList = () => {
    if (listItems.length === 0) return
    if (isNumbered) {
      elements.push(
        <ol key={`ol-${lineIdx}`} className="list-decimal list-outside ml-5 space-y-1 my-2">
          {listItems.map((item, idx) => (
            <li key={idx} className="text-sm">
              {renderFormattedText(item)}
            </li>
          ))}
        </ol>
      )
    } else {
      elements.push(
        <ul key={`ul-${lineIdx}`} className="list-disc list-outside ml-5 space-y-1 my-2">
          {listItems.map((item, idx) => (
            <li key={idx} className="text-sm">
              {renderFormattedText(item)}
            </li>
          ))}
        </ul>
      )
    }
    listItems = []
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()

    if (!trimmed) {
      flushList()
      continue
    }

    // Headings
    if (trimmed.startsWith('#### ')) {
      flushList()
      elements.push(
        <h5 key={`h4-${i}`} className="font-display font-semibold text-sm text-[var(--text-primary)] mt-2.5 mb-1">
          {renderFormattedText(trimmed.slice(5))}
        </h5>
      )
      continue
    }
    if (trimmed.startsWith('### ')) {
      flushList()
      elements.push(
        <h4 key={`h3-${i}`} className="font-display font-semibold text-base text-[var(--text-primary)] mt-3 mb-1">
          {renderFormattedText(trimmed.slice(4))}
        </h4>
      )
      continue
    }
    if (trimmed.startsWith('## ')) {
      flushList()
      elements.push(
        <h3 key={`h2-${i}`} className="font-display font-bold text-lg text-[var(--text-primary)] mt-4 mb-1.5">
          {renderFormattedText(trimmed.slice(3))}
        </h3>
      )
      continue
    }
    if (trimmed.startsWith('# ')) {
      flushList()
      elements.push(
        <h2 key={`h1-${i}`} className="font-display font-bold text-xl text-[var(--text-primary)] mt-4 mb-2">
          {renderFormattedText(trimmed.slice(2))}
        </h2>
      )
      continue
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      flushList()
      elements.push(
        <blockquote
          key={`quote-${i}`}
          className="border-l-3 border-purple-500/50 pl-3.5 py-1 my-2 bg-purple-500/5 rounded-r-lg text-xs italic text-[var(--text-secondary)]"
        >
          {renderFormattedText(trimmed.slice(2))}
        </blockquote>
      )
      continue
    }

    // Unordered List
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (isNumbered && listItems.length > 0) flushList()
      isNumbered = false
      listItems.push(trimmed.slice(2))
      continue
    }

    // Ordered List
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/)
    if (numMatch) {
      if (!isNumbered && listItems.length > 0) flushList()
      isNumbered = true
      listItems.push(numMatch[2])
      continue
    }

    // Regular paragraph
    flushList()
    elements.push(
      <p key={`p-${i}`} className="text-sm leading-relaxed">
        {renderFormattedText(line)}
      </p>
    )
  }

  flushList()
  return elements
}
