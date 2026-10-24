import React from 'react'
import { CheckCircle2, AlertCircle, Clock, Info } from 'lucide-react'
import type { AttemptResponse } from '../../types/activity'

interface SubmissionFeedbackProps {
  attempt: AttemptResponse
  passingScore: number
}

export const SubmissionFeedback: React.FC<SubmissionFeedbackProps> = ({
  attempt,
  passingScore,
}) => {
  const isPassed = attempt.passed === true
  const isReviewRequired = attempt.status === 'review_required'
  const isSubmittedOnly = attempt.status === 'submitted' && attempt.score === null

  const feedback = attempt.feedback || {}
  const message = feedback.message || (isPassed ? 'Congratulations! You passed this assessment.' : 'Score below passing threshold.')
  const explanation = feedback.explanation

  // Determine badge styling
  let badgeColor = 'bg-state-error/15 text-state-error border-state-error/30'
  let Icon = AlertCircle
  let title = 'Assessment Not Passed'

  if (isReviewRequired) {
    badgeColor = 'bg-accent-cyan/15 text-accent-cyan border-accent-cyan/30'
    Icon = Clock
    title = 'Submitted for Review'
  } else if (isSubmittedOnly) {
    badgeColor = 'bg-accent-violet/15 text-accent-violet border-accent-violet/30'
    Icon = Info
    title = 'Submission Received'
  } else if (isPassed) {
    badgeColor = 'bg-state-success/15 text-state-success border-state-success/30'
    Icon = CheckCircle2
    title = 'Assessment Passed!'
  }

  return (
    <div
      role="region"
      aria-label="Assessment Feedback"
      className="p-4 sm:p-5 rounded-xl bg-bg-surface border border-border-medium space-y-4 animate-fadeIn my-4"
    >
      {/* Header bar with Score and Status */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
            <Icon className="w-3.5 h-3.5" />
            <span>{title}</span>
          </span>
          <span className="text-xs font-mono text-text-muted">
            Attempt #{attempt.attempt_number}
          </span>
        </div>

        {attempt.score !== null && (
          <div className="flex items-baseline gap-1 font-mono">
            <span className="text-xs text-text-muted">Score:</span>
            <span
              className={`text-xl font-extrabold ${
                isPassed ? 'text-state-success' : 'text-state-error'
              }`}
            >
              {attempt.score}%
            </span>
            <span className="text-xs text-text-muted">/ Pass {passingScore}%</span>
          </div>
        )}
      </div>

      {/* Main Feedback Message */}
      <div className="text-sm text-text-primary leading-relaxed font-medium">
        {message}
      </div>

      {/* Optional Explanation Text */}
      {explanation && (
        <div className="p-3.5 rounded-lg bg-bg-elevated/70 border border-border-subtle text-xs sm:text-sm text-text-secondary leading-relaxed">
          <span className="font-semibold text-text-primary mr-1.5">Explanation:</span>
          <span>{explanation}</span>
        </div>
      )}

      {/* Criteria / Details Breakdown if available */}
      {feedback.breakdown && typeof feedback.breakdown === 'object' && (
        <div className="pt-2 text-xs font-mono text-text-muted flex flex-wrap gap-3">
          {Object.entries(feedback.breakdown).map(([k, v]) => (
            <span key={k} className="bg-bg-elevated px-2 py-0.5 rounded border border-border-subtle">
              {k.replace(/_/g, ' ')}: <strong className="text-text-primary">{String(v)}</strong>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
