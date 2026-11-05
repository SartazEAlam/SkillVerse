import React from 'react'
import { Award, ShieldAlert, CheckCircle, Scale } from 'lucide-react'
import type { EvaluationCriteria } from '../../types/project'

interface RubricViewProps {
  criteria: EvaluationCriteria
}

export const RubricView: React.FC<RubricViewProps> = ({ criteria }) => {
  const rubricList = criteria?.rubric || []

  return (
    <div className="space-y-4">
      {/* Rubric Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-accent-cyan/20 bg-accent-cyan/5 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-accent-cyan/10 p-2 text-accent-cyan">
            <Award className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary">
              Evaluation Rubric & Passing Standard
            </h3>
            <p className="text-xs text-text-secondary">
              Submissions are evaluated against standard mastery criteria by a course instructor.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-md bg-bg-surface px-3 py-1.5 border border-border-subtle text-xs">
          <CheckCircle className="h-4 w-4 text-state-success" aria-hidden="true" />
          <span className="text-text-muted">Required to Pass:</span>
          <strong className="text-text-primary font-mono font-semibold">
            {criteria.passing_score ?? 70}%
          </strong>
        </div>
      </div>

      {/* Criteria Cards */}
      {rubricList.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rubricList.map((criterion, idx) => (
            <div
              key={criterion.id || `crit-${idx}`}
              className="rounded-lg border border-border-subtle bg-bg-surface/50 p-4 transition-colors hover:border-border-medium"
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                  <Scale className="h-3.5 w-3.5 text-accent-violet shrink-0" aria-hidden="true" />
                  <span>{criterion.title}</span>
                </h4>
                <span className="shrink-0 rounded bg-bg-elevated px-2 py-0.5 text-xs font-mono font-medium text-accent-cyan border border-border-subtle">
                  Max: {criterion.max_score} pts
                </span>
              </div>

              {criterion.description && (
                <p className="mt-2 text-xs text-text-secondary leading-relaxed">
                  {criterion.description}
                </p>
              )}

              {criterion.weight && criterion.weight !== 1.0 && (
                <div className="mt-3 text-[11px] text-text-muted">
                  Weight factor: <span className="font-mono text-text-secondary">{criterion.weight}x</span>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-border-subtle bg-bg-surface/30 p-4 text-center text-xs text-text-muted">
          Holistic evaluator assessment (Standard rubric applied upon review).
        </div>
      )}

      {/* Security & Integrity Note */}
      <div className="flex items-start gap-2.5 rounded-lg border border-border-subtle bg-bg-surface/30 p-3 text-xs text-text-muted">
        <ShieldAlert className="h-4 w-4 text-accent-violet shrink-0 mt-0.5" aria-hidden="true" />
        <p className="leading-relaxed">
          <strong className="text-text-secondary">Integrity Protection:</strong> Evaluator private scoring keys, instructor model solutions, and internal reviewer notes are protected to ensure authentic, rigorous competency assessment.
        </p>
      </div>
    </div>
  )
}
