import React from 'react'
import { CheckCircle2, Circle, ListOrdered } from 'lucide-react'
import type { Milestone } from '../../types/project'

interface MilestoneListProps {
  milestones?: Milestone[]
  completedIds?: string[]
  isInteractive?: boolean
  onToggleMilestone?: (milestoneId: string) => void
}

export const MilestoneList: React.FC<MilestoneListProps> = ({
  milestones = [],
  completedIds = [],
  isInteractive = false,
  onToggleMilestone,
}) => {
  if (!milestones || milestones.length === 0) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-surface/50 p-4 text-center text-xs text-text-muted">
        No specific milestones defined for this project.
      </div>
    )
  }

  const completedCount = milestones.filter((m) => completedIds.includes(m.id)).length
  const pct = Math.round((completedCount / milestones.length) * 100)

  return (
    <div className="space-y-3">
      {/* Progress header if interactive or some milestones completed */}
      <div className="flex items-center justify-between text-xs text-text-muted">
        <span className="flex items-center gap-1.5 font-medium text-text-secondary">
          <ListOrdered className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
          <span>Milestones Progress</span>
        </span>
        <span className="font-mono">
          {completedCount} of {milestones.length} completed ({pct}%)
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-bg-surface"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Milestones completion progress"
      >
        <div
          className="h-full bg-gradient-to-r from-accent-cyan to-accent-violet transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Milestone items */}
      <ul className="space-y-2 pt-1" aria-label="Project Milestones">
        {milestones.map((milestone, idx) => {
          const isCompleted = completedIds.includes(milestone.id)

          if (isInteractive) {
            return (
              <li key={milestone.id}>
                <label
                  className={`flex items-start gap-3 rounded-lg border p-3 transition-colors cursor-pointer select-none ${
                    isCompleted
                      ? 'border-state-success/30 bg-state-success/5'
                      : 'border-border-subtle bg-bg-surface/40 hover:bg-bg-surface hover:border-border-medium'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isCompleted}
                    onChange={() => onToggleMilestone && onToggleMilestone(milestone.id)}
                    className="mt-0.5 h-4 w-4 rounded border-border-medium bg-bg-base text-accent-violet focus:ring-accent-violet focus:ring-offset-bg-base cursor-pointer"
                    aria-label={`Mark milestone ${milestone.title} as ${isCompleted ? 'incomplete' : 'completed'}`}
                  />
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-sm font-medium ${
                        isCompleted
                          ? 'text-text-primary line-through decoration-text-muted/60'
                          : 'text-text-primary'
                      }`}
                    >
                      {idx + 1}. {milestone.title}
                    </span>
                    {milestone.description && (
                      <p className="mt-0.5 text-xs text-text-secondary leading-relaxed">
                        {milestone.description}
                      </p>
                    )}
                  </div>
                </label>
              </li>
            )
          }

          return (
            <li
              key={milestone.id}
              className={`flex items-start gap-3 rounded-lg border p-3 ${
                isCompleted
                  ? 'border-state-success/30 bg-state-success/5'
                  : 'border-border-subtle bg-bg-surface/40'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2
                  className="mt-0.5 h-4 w-4 text-state-success shrink-0"
                  aria-hidden="true"
                />
              ) : (
                <Circle
                  className="mt-0.5 h-4 w-4 text-text-muted shrink-0"
                  aria-hidden="true"
                />
              )}
              <div className="flex-1 min-w-0">
                <span
                  className={`text-sm font-medium ${
                    isCompleted ? 'text-text-primary' : 'text-text-secondary'
                  }`}
                >
                  {idx + 1}. {milestone.title}
                </span>
                {milestone.description && (
                  <p className="mt-0.5 text-xs text-text-muted leading-relaxed">
                    {milestone.description}
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

