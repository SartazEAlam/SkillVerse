import React, { useMemo } from 'react'
import { ArrowRight, Check, HelpCircle } from 'lucide-react'
import type { MatchingItem } from '../../types/activity'

interface MatchingActivityProps {
  leftItems: MatchingItem[]
  rightItems: MatchingItem[]
  pairs: Record<string, string>
  onChange: (leftId: string, rightId: string) => void
  disabled?: boolean
}

export const MatchingActivity: React.FC<MatchingActivityProps> = ({
  leftItems = [],
  rightItems = [],
  pairs = {},
  onChange,
  disabled = false,
}) => {
  const matchedCount = useMemo(() => {
    return leftItems.filter((item) => Boolean(pairs[item.id])).length
  }, [leftItems, pairs])

  return (
    <div className="space-y-4 my-4 font-sans">
      <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-text-muted">
        <span>Match each item with its corresponding partner:</span>
        <span
          className={`font-semibold ${
            matchedCount === leftItems.length && leftItems.length > 0
              ? 'text-accent-emerald'
              : 'text-text-muted'
          }`}
        >
          {matchedCount} of {leftItems.length} Matched
        </span>
      </div>

      {/* Screen reader live region */}
      <div aria-live="polite" className="sr-only">
        {matchedCount === leftItems.length
          ? 'All items have been matched.'
          : `${matchedCount} of ${leftItems.length} items currently matched.`}
      </div>

      <div role="group" aria-label="Matching exercise" className="space-y-3">
        {leftItems.map((leftItem) => {
          const selectedRightId = pairs[leftItem.id] || ''
          const isMatched = Boolean(selectedRightId)

          return (
            <div
              key={leftItem.id}
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:p-4 rounded-xl border transition-all ${
                isMatched
                  ? 'bg-bg-surface border-accent-emerald/30'
                  : 'bg-bg-surface border-border-subtle hover:border-border-medium'
              }`}
            >
              {/* Left Item Description */}
              <div className="sm:w-1/2 text-sm font-medium text-text-primary leading-relaxed flex items-center gap-2.5">
                <span
                  className={`w-2.5 h-2.5 rounded-full shrink-0 transition-colors ${
                    isMatched ? 'bg-accent-emerald' : 'bg-accent-violet'
                  }`}
                  aria-hidden="true"
                />
                <span>{leftItem.text}</span>
              </div>

              {/* Arrow connector */}
              <div className="hidden sm:flex items-center text-text-muted shrink-0">
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </div>

              {/* Right Item Selector */}
              <div className="sm:w-1/2 flex items-center gap-2">
                <label htmlFor={`match-select-${leftItem.id}`} className="sr-only">
                  Match for {leftItem.text}
                </label>
                <select
                  id={`match-select-${leftItem.id}`}
                  aria-label={`Match for ${leftItem.text}`}
                  value={selectedRightId}
                  disabled={disabled}
                  onChange={(e) => onChange(leftItem.id, e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet disabled:opacity-70 disabled:cursor-not-allowed font-sans cursor-pointer transition-all"
                >
                  <option value="">-- Select Match --</option>
                  {rightItems.map((rightItem) => (
                    <option key={rightItem.id} value={rightItem.id}>
                      {rightItem.text}
                    </option>
                  ))}
                </select>

                <div className="w-6 flex items-center justify-center shrink-0">
                  {isMatched ? (
                    <Check
                      className="w-4 h-4 text-accent-emerald"
                      aria-label="Matched"
                    />
                  ) : (
                    <HelpCircle
                      className="w-4 h-4 text-text-muted/40"
                      aria-label="Unmatched"
                    />
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
