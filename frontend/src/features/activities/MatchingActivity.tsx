import React from 'react'
import { ArrowRight } from 'lucide-react'
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
  return (
    <div className="space-y-4 my-4">
      <div className="text-xs font-mono uppercase tracking-wider text-text-muted">
        <span>Match each item on the left with its corresponding item on the right:</span>
      </div>

      <div className="space-y-3">
        {leftItems.map((leftItem) => {
          const selectedRightId = pairs[leftItem.id] || ''

          return (
            <div
              key={leftItem.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:p-4 rounded-xl bg-bg-surface border border-border-subtle hover:border-border-medium transition-all"
            >
              {/* Left Item Description */}
              <div className="sm:w-1/2 text-sm font-medium text-text-primary leading-relaxed flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-violet shrink-0" />
                <span>{leftItem.text}</span>
              </div>

              {/* Arrow connector */}
              <div className="hidden sm:flex items-center text-text-muted shrink-0">
                <ArrowRight className="w-4 h-4" />
              </div>

              {/* Right Item Selector */}
              <div className="sm:w-1/2">
                <select
                  aria-label={`Match for ${leftItem.text}`}
                  value={selectedRightId}
                  disabled={disabled}
                  onChange={(e) => onChange(leftItem.id, e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet disabled:opacity-70 disabled:cursor-not-allowed font-sans cursor-pointer"
                >
                  <option value="" disabled>
                    -- Select Match --
                  </option>
                  {rightItems.map((rightItem) => (
                    <option key={rightItem.id} value={rightItem.id}>
                      {rightItem.text}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
