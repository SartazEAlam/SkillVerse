import React from 'react'
import type { ListBlockContent } from '../../../types/lesson'

interface ListBlockProps {
  content: ListBlockContent
}

function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
  let lastIdx = 0
  let match: RegExpExecArray | null

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index))
    }
    const token = match[0]
    const key = `list-inline-${match.index}`

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

export const ListBlock: React.FC<ListBlockProps> = ({ content }) => {
  const { ordered = false, items = [] } = content
  if (!items || items.length === 0) return null

  if (ordered) {
    return (
      <ol className="my-4 space-y-2 list-decimal list-outside pl-6 text-sm sm:text-base text-text-secondary leading-relaxed">
        {items.map((item, idx) => (
          <li key={idx} className="pl-1">
            {renderInlineMarkdown(item)}
          </li>
        ))}
      </ol>
    )
  }

  return (
    <ul className="my-4 space-y-2 list-disc list-outside pl-6 text-sm sm:text-base text-text-secondary leading-relaxed marker:text-accent-violet">
      {items.map((item, idx) => (
        <li key={idx} className="pl-1">
          {renderInlineMarkdown(item)}
        </li>
      ))}
    </ul>
  )
}
