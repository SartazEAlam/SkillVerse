import React from 'react'
import type { TextBlockContent } from '../../../types/lesson'

interface TextBlockProps {
  content: TextBlockContent
}

/**
 * Strip dangerous HTML script tags, event handlers, and javascript: protocols.
 */
function sanitizeText(raw: string): string {
  if (!raw) return ''
  return raw
    .replace(/<\s*(script|style|iframe|object|embed|form|meta|base)\b[^>]*>.*?<\/\s*\1\s*>/gis, '')
    .replace(/<\s*(script|style|iframe|object|embed|form|meta|base)\b[^>]*\/>/gis, '')
    .replace(/\bon\w+\s*=\s*(['"]).*?\1/gis, '')
    .replace(/javascript\s*:/gis, '')
}

/**
 * Render lightweight markdown tokens (bold, italic, code, links, blockquotes) safely as React nodes.
 */
function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  // Regex to split on bold (**text**), italic (*text*), inline code (`code`), or links ([text](url))
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g

  let lastIdx = 0
  let match: RegExpExecArray | null

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index))
    }

    const token = match[0]
    const key = `inline-${match.index}`

    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={key} className="font-semibold text-text-primary">
          {token.slice(2, -2)}
        </strong>
      )
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={key} className="italic text-text-primary">
          {token.slice(1, -1)}
        </em>
      )
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={key}
          className="px-1.5 py-0.5 rounded text-xs font-mono bg-bg-surface text-accent-violet border border-border-subtle"
        >
          {token.slice(1, -1)}
        </code>
      )
    } else if (token.startsWith('[') && token.includes('](') && token.endsWith(')')) {
      const splitIdx = token.indexOf('](')
      const label = token.slice(1, splitIdx)
      const rawUrl = token.slice(splitIdx + 2, -1)
      const safeUrl =
        rawUrl.startsWith('http://') || rawUrl.startsWith('https://') || rawUrl.startsWith('/')
          ? rawUrl
          : '#'
      parts.push(
        <a
          key={key}
          href={safeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent-cyan hover:underline font-medium focus-visible:ring-1 focus-visible:ring-accent-cyan"
        >
          {label}
        </a>
      )
    } else {
      parts.push(token)
    }

    lastIdx = match.index + token.length
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx))
  }

  return parts
}

export const TextBlock: React.FC<TextBlockProps> = ({ content }) => {
  const rawText = content.text || (content as unknown as { content?: string }).content || ''
  const sanitized = sanitizeText(rawText)
  if (!sanitized) return null

  // Plain format: render single paragraph with preserved whitespace
  if (content.format === 'plain') {
    return (
      <div className="my-4 text-sm sm:text-base text-text-secondary leading-relaxed whitespace-pre-line">
        {sanitized}
      </div>
    )
  }

  // Markdown format: split into paragraphs or blockquotes
  const blocks = sanitized.split(/\n\s*\n/)

  return (
    <div className="my-4 space-y-4 text-sm sm:text-base text-text-secondary leading-relaxed">
      {blocks.map((block, idx) => {
        const trimmed = block.trim()
        if (!trimmed) return null

        if (trimmed.startsWith('>')) {
          const quoteText = trimmed.replace(/^>\s*/gm, '')
          return (
            <blockquote
              key={idx}
              className="border-l-4 border-accent-violet/60 pl-4 py-2 my-4 bg-bg-elevated/40 rounded-r-lg italic text-text-secondary"
            >
              {renderInlineMarkdown(quoteText)}
            </blockquote>
          )
        }

        return <p key={idx}>{renderInlineMarkdown(trimmed)}</p>
      })}
    </div>
  )
}
