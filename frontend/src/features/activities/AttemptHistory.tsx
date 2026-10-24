import React, { useState } from 'react'
import { History, ChevronDown, ChevronUp, Check, X, Clock } from 'lucide-react'
import type { AttemptResponse } from '../../types/activity'

interface AttemptHistoryProps {
  attempts: AttemptResponse[]
}

export const AttemptHistory: React.FC<AttemptHistoryProps> = ({ attempts = [] }) => {
  const [isOpen, setIsOpen] = useState(false)

  if (attempts.length === 0) return null

  return (
    <div className="pt-2 text-xs font-mono">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-text-muted hover:text-text-primary transition-colors py-1 cursor-pointer select-none"
      >
        <History className="w-3.5 h-3.5 text-accent-cyan" />
        <span>Past Attempts ({attempts.length})</span>
        {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="mt-2 space-y-1.5 p-3 rounded-xl bg-bg-surface border border-border-subtle animate-fadeIn">
          {attempts.map((att) => {
            const dateStr = new Date(att.started_at).toLocaleString()
            const isPassed = att.passed === true

            return (
              <div
                key={att.id}
                className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-bg-elevated/50 text-text-secondary text-[11px]"
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold text-text-primary">#{att.attempt_number}</span>
                  <span className="text-text-muted">{dateStr}</span>
                </div>

                <div className="flex items-center gap-2">
                  {att.score !== null ? (
                    <span className="font-bold text-text-primary">{att.score}%</span>
                  ) : (
                    <span className="text-text-muted">--</span>
                  )}

                  {att.status === 'review_required' ? (
                    <span className="flex items-center text-accent-cyan" title="Review Required">
                      <Clock className="w-3 h-3" />
                    </span>
                  ) : isPassed ? (
                    <span className="flex items-center text-state-success" title="Passed">
                      <Check className="w-3 h-3" />
                    </span>
                  ) : (
                    <span className="flex items-center text-state-error" title="Failed">
                      <X className="w-3 h-3" />
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
