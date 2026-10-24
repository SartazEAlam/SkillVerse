import React from 'react'
import type { BlankItem } from '../../types/activity'

interface FillBlankActivityProps {
  template?: string
  blanks: BlankItem[]
  values: Record<string, string>
  onChange: (blankId: string, val: string) => void
  disabled?: boolean
}

export const FillBlankActivity: React.FC<FillBlankActivityProps> = ({
  template,
  blanks = [],
  values = {},
  onChange,
  disabled = false,
}) => {
  // If a template string is provided with [blank_id] placeholders, render inline
  if (template) {
    const parts = template.split(/(\[[a-zA-Z0-9_-]+\])/g)

    return (
      <div className="space-y-4 my-4">
        <div className="p-4 sm:p-5 rounded-xl bg-bg-surface border border-border-medium text-sm sm:text-base leading-loose text-text-primary">
          {parts.map((part, idx) => {
            const match = part.match(/^\[([a-zA-Z0-9_-]+)\]$/)
            if (match) {
              const blankId = match[1]
              const blankDef = blanks.find((b) => b.id === blankId) || { id: blankId }
              return (
                <span key={idx} className="inline-block mx-1.5 align-baseline">
                  <input
                    type="text"
                    aria-label={`Fill blank ${blankId}`}
                    value={values[blankId] || ''}
                    disabled={disabled}
                    placeholder={blankDef.hint || '...'}
                    onChange={(e) => onChange(blankId, e.target.value)}
                    className="inline-block px-3 py-1 w-32 sm:w-40 rounded-lg bg-bg-elevated border border-accent-cyan/60 text-text-primary text-sm font-mono placeholder:text-text-muted focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan text-center disabled:opacity-70 disabled:cursor-not-allowed"
                  />
                </span>
              )
            }
            return <span key={idx}>{part}</span>
          })}
        </div>
      </div>
    )
  }

  // Fallback: list of blank fields with hints
  return (
    <div className="space-y-3 my-4">
      {blanks.map((blank, idx) => (
        <div
          key={blank.id}
          className="flex flex-col sm:flex-row sm:items-center gap-2 p-3.5 rounded-xl bg-bg-surface border border-border-subtle"
        >
          <label
            htmlFor={`blank-${blank.id}`}
            className="text-sm font-medium text-text-secondary sm:w-1/3"
          >
            <span className="font-mono text-xs text-accent-cyan mr-1">#{idx + 1}</span>
            {blank.hint || blank.id}:
          </label>
          <input
            id={`blank-${blank.id}`}
            type="text"
            value={values[blank.id] || ''}
            disabled={disabled}
            placeholder="Type answer..."
            onChange={(e) => onChange(blank.id, e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-text-primary text-sm font-mono placeholder:text-text-muted focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan disabled:opacity-70 disabled:cursor-not-allowed"
          />
        </div>
      ))}
    </div>
  )
}
