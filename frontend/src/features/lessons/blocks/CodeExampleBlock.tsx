import React, { useState } from 'react'
import { Check, Copy, Terminal } from 'lucide-react'
import type { CodeExampleBlockContent } from '../../../types/lesson'

interface CodeExampleBlockProps {
  content: CodeExampleBlockContent
}

/**
 * Tokenize a single line of code into syntax-colored spans based on language.
 */
function highlightCodeLine(line: string, language: string): React.ReactNode {
  const lang = (language || 'text').toLowerCase()

  // 1. Comments
  if (
    (lang === 'python' && line.trim().startsWith('#')) ||
    (['javascript', 'typescript', 'js', 'ts', 'css'].includes(lang) &&
      (line.trim().startsWith('//') || line.trim().startsWith('/*'))) ||
    (lang === 'sql' && line.trim().startsWith('--')) ||
    (lang === 'html' && line.trim().startsWith('<!--'))
  ) {
    return <span className="text-text-muted italic">{line}</span>
  }

  // Common keywords regex
  let keywordRegex: RegExp | null = null
  if (['javascript', 'typescript', 'js', 'ts'].includes(lang)) {
    keywordRegex =
      /\b(const|let|var|function|return|if|else|for|while|import|from|export|default|class|new|this|async|await|try|catch|throw|typeof|instanceof|true|false|null|undefined)\b/g
  } else if (lang === 'python') {
    keywordRegex =
      /\b(def|class|return|import|from|as|if|elif|else|while|for|in|try|except|finally|raise|with|pass|lambda|True|False|None|self|async|await)\b/g
  } else if (lang === 'sql') {
    keywordRegex =
      /\b(SELECT|FROM|WHERE|INSERT|INTO|UPDATE|SET|DELETE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|AND|OR|NOT|NULL|PRIMARY|KEY|FOREIGN|REFERENCES|TABLE|CREATE|DROP|ALTER)\b/gi
  }

  // Tokenize line by strings and keywords
  const tokens: React.ReactNode[] = []
  // Matches strings ("...", '...', `...`)
  const stringRegex = /(".*?"|'.*?'|`.*?`)/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = stringRegex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      const before = line.substring(lastIndex, match.index)
      tokens.push(highlightKeywords(before, keywordRegex, `before-${match.index}`))
    }

    tokens.push(
      <span key={`str-${match.index}`} className="text-emerald-400">
        {match[0]}
      </span>
    )
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < line.length) {
    const after = line.substring(lastIndex)
    tokens.push(highlightKeywords(after, keywordRegex, `after-${lastIndex}`))
  }

  return tokens.length > 0 ? tokens : line
}

function highlightKeywords(
  text: string,
  keywordRegex: RegExp | null,
  keyPrefix: string
): React.ReactNode {
  if (!keywordRegex) return text

  const parts: React.ReactNode[] = []
  let lastIdx = 0
  let m: RegExpExecArray | null
  const regex = new RegExp(keywordRegex.source, keywordRegex.flags)

  while ((m = regex.exec(text)) !== null) {
    if (m.index > lastIdx) {
      parts.push(text.substring(lastIdx, m.index))
    }
    parts.push(
      <span key={`${keyPrefix}-kw-${m.index}`} className="text-accent-violet font-semibold">
        {m[0]}
      </span>
    )
    lastIdx = m.index + m[0].length
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx))
  }

  return parts
}

export const CodeExampleBlock: React.FC<CodeExampleBlockProps> = ({ content }) => {
  const [copied, setCopied] = useState(false)
  const code = content.code || ''
  const language = content.language || 'text'
  const caption = content.caption
  const showLineNumbers = content.show_line_numbers ?? true

  const handleCopy = async () => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(code)
      } else {
        // Fallback for non-secure / test environments
        const textArea = document.createElement('textarea')
        textArea.value = code
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // In case clipboard permissions are denied
      setCopied(false)
    }
  }

  const lines = code.split('\n')

  return (
    <div className="my-6 rounded-xl border border-border-medium bg-bg-inset overflow-hidden shadow-lg">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-bg-surface/70 border-b border-border-subtle text-xs">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-accent-cyan" />
          <span className="font-mono font-medium uppercase tracking-wider text-accent-cyan text-[11px]">
            {language}
          </span>
          {caption && (
            <>
              <span className="text-border-medium">•</span>
              <span className="text-text-secondary truncate max-w-xs sm:max-w-md font-mono text-[11px]">
                {caption}
              </span>
            </>
          )}
        </div>

        {/* Copy Button */}
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? 'Code copied to clipboard' : 'Copy code to clipboard'}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition-colors text-text-secondary hover:text-text-primary hover:bg-bg-elevated cursor-pointer focus-visible:ring-1 focus-visible:ring-accent-violet"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-state-success" />
              <span className="text-state-success font-medium">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content Area */}
      <div className="p-4 overflow-x-auto text-xs sm:text-sm font-mono leading-relaxed selection:bg-accent-violet/30">
        <pre className="table w-full">
          <code>
            {lines.map((line, idx) => (
              <div key={idx} className="table-row">
                {showLineNumbers && (
                  <span
                    aria-hidden="true"
                    className="table-cell text-right pr-4 select-none text-text-muted/40 font-mono text-xs w-8"
                  >
                    {idx + 1}
                  </span>
                )}
                <span className="table-cell whitespace-pre">
                  {highlightCodeLine(line, language)}
                </span>
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  )
}
