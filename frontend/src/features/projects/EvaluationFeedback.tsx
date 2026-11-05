import React from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  User,
  Calendar,
  MessageSquare,
} from 'lucide-react'
import type { EvaluationResult, RubricCriterion } from '../../types/project'

interface EvaluationFeedbackProps {
  evaluation: EvaluationResult | null | undefined
  rubricCriteria?: RubricCriterion[]
  evaluatorName?: string | null
  evaluatedAt?: string | null
  status: string
}

export const EvaluationFeedback: React.FC<EvaluationFeedbackProps> = ({
  evaluation,
  rubricCriteria = [],
  evaluatorName,
  evaluatedAt,
  status,
}) => {
  if (!evaluation) {
    return null
  }

  const passed = evaluation.passed ?? (status === 'COMPLETED')
  const score = evaluation.score ?? 0
  const passingScore = evaluation.passing_score ?? 70

  // Build rubric lookup map for titles and max scores
  const rubricMap = new Map<string, RubricCriterion>()
  rubricCriteria.forEach((c) => {
    rubricMap.set(c.id, c)
  })

  return (
    <div
      className={`rounded-xl border p-5 sm:p-6 transition-all ${
        passed
          ? 'border-state-success/30 bg-state-success/5'
          : 'border-state-warning/30 bg-state-warning/5'
      }`}
    >
      {/* Top Header: Score & Outcome */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle/60 pb-5">
        <div className="flex items-center gap-3">
          <div
            className={`rounded-xl p-3 ${
              passed
                ? 'bg-state-success/15 text-state-success'
                : 'bg-state-warning/15 text-state-warning'
            }`}
          >
            {passed ? (
              <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
            ) : (
              <AlertTriangle className="h-6 w-6" aria-hidden="true" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-text-primary">
                {passed ? 'Project Evaluation Passed' : 'Revision & Changes Requested'}
              </h3>
              <span
                className={`rounded px-2 py-0.5 text-xs font-semibold ${
                  passed
                    ? 'bg-state-success/20 text-state-success'
                    : 'bg-state-warning/20 text-state-warning'
                }`}
              >
                {passed ? 'COMPLETED' : 'CHANGES REQUESTED'}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-text-secondary">
              {passed
                ? 'Your submission successfully satisfied all rubric requirements.'
                : 'Your submission requires revisions before mastery credit can be awarded.'}
            </p>
          </div>
        </div>

        {/* Score pill */}
        <div className="flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-surface px-4 py-2">
          <div className="text-right">
            <div className="text-[11px] text-text-muted">Final Score</div>
            <div className="text-xl font-bold font-mono text-text-primary">
              <span className={passed ? 'text-state-success' : 'text-state-warning'}>
                {score.toFixed(1)}
              </span>
              <span className="text-sm font-normal text-text-muted"> / 100</span>
            </div>
          </div>
          <div className="h-8 w-px bg-border-subtle" />
          <div className="text-left text-[11px] text-text-muted">
            <div>Passing Target:</div>
            <div className="font-mono font-semibold text-text-secondary">{passingScore}%</div>
          </div>
        </div>
      </div>

      {/* Evaluator General Feedback */}
      <div className="mt-5 space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
          <MessageSquare className="h-3.5 w-3.5 text-accent-violet" aria-hidden="true" />
          <span>Evaluator Feedback</span>
        </div>
        <div className="rounded-lg border border-border-subtle bg-bg-surface/70 p-4 text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
          {evaluation.feedback || 'No written feedback provided by the reviewer.'}
        </div>
      </div>

      {/* Criteria Breakdown */}
      {evaluation.criteria_scores && evaluation.criteria_scores.length > 0 && (
        <div className="mt-5 space-y-3">
          <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Rubric Criteria Breakdown
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {evaluation.criteria_scores.map((cs) => {
              const criterionMeta = rubricMap.get(cs.criterion_id)
              const title = criterionMeta?.title || cs.criterion_id
              const maxScore = criterionMeta?.max_score

              return (
                <div
                  key={cs.criterion_id}
                  className="rounded-lg border border-border-subtle bg-bg-surface/50 p-3.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-text-primary">{title}</span>
                    <span className="shrink-0 rounded bg-bg-elevated px-2 py-0.5 text-xs font-mono font-medium text-text-secondary border border-border-subtle">
                      {cs.score} {maxScore ? `/ ${maxScore} pts` : 'pts'}
                    </span>
                  </div>

                  {cs.feedback && (
                    <p className="mt-2 text-xs text-text-secondary leading-relaxed border-t border-border-subtle/50 pt-2">
                      {cs.feedback}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Meta Footer */}
      {(evaluatorName || evaluatedAt) && (
        <div className="mt-5 flex flex-wrap items-center gap-4 border-t border-border-subtle/40 pt-4 text-xs text-text-muted">
          {evaluatorName && (
            <div className="flex items-center gap-1.5">
              <User className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
              <span>Evaluated by <strong className="text-text-secondary">{evaluatorName}</strong></span>
            </div>
          )}
          {evaluatedAt && (
            <div className="flex items-center gap-1.5 font-mono">
              <Calendar className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
              <span>{new Date(evaluatedAt).toLocaleString()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
