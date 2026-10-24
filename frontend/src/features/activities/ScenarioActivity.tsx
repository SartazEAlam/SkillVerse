import React from 'react'
import type { ScenarioDecision } from '../../types/activity'

interface ScenarioActivityProps {
  scenarioText?: string
  decisions: ScenarioDecision[]
  selectedDecisionId: string | null
  onChange: (decisionId: string) => void
  disabled?: boolean
}

export const ScenarioActivity: React.FC<ScenarioActivityProps> = ({
  scenarioText,
  decisions = [],
  selectedDecisionId,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-4 my-4">
      {scenarioText && (
        <div className="p-4 sm:p-5 rounded-xl bg-bg-surface border border-border-medium text-sm sm:text-base text-text-primary leading-relaxed">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-accent-cyan mb-2">
            Scenario Background
          </div>
          <p>{scenarioText}</p>
        </div>
      )}

      <div className="text-xs font-mono uppercase tracking-wider text-text-muted">
        <span>Choose the optimal professional course of action:</span>
      </div>

      <div
        role="radiogroup"
        aria-label="Scenario decision options"
        className="space-y-3"
      >
        {decisions.map((decision, index) => {
          const isSelected = selectedDecisionId === decision.id

          return (
            <label
              key={decision.id}
              htmlFor={`decision-${decision.id}`}
              className={`block p-4 rounded-xl border transition-all cursor-pointer select-none ${
                isSelected
                  ? 'bg-accent-violet/15 border-accent-violet text-text-primary shadow-[0_0_16px_rgba(139,92,246,0.25)]'
                  : 'bg-bg-surface border-border-subtle hover:border-border-medium hover:bg-bg-elevated text-text-secondary'
              } ${disabled ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="radio"
                  id={`decision-${decision.id}`}
                  name="scenario-decision"
                  value={decision.id}
                  checked={isSelected}
                  disabled={disabled}
                  onChange={() => onChange(decision.id)}
                  className="mt-1 h-4 w-4 text-accent-violet border-border-medium focus:ring-accent-violet shrink-0"
                />
                <div className="space-y-1">
                  <div className="text-sm sm:text-base font-semibold text-text-primary flex items-center gap-2">
                    <span className="font-mono text-xs text-text-muted">
                      Decision {String.fromCharCode(65 + index)}:
                    </span>
                    <span>{decision.title}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                    {decision.description}
                  </p>
                </div>
              </div>
            </label>
          )
        })}
      </div>
    </div>
  )
}
