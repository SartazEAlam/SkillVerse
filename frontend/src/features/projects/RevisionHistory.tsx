import React from 'react'
import { History, GitCommit, ArrowRight, CheckCircle2, Clock, AlertTriangle } from 'lucide-react'
import type { SubmissionSummary } from '../../types/project'
import { Link } from 'react-router-dom'

interface RevisionHistoryProps {
  currentSubmissionId: string
  submissions: SubmissionSummary[]
}

export const RevisionHistory: React.FC<RevisionHistoryProps> = ({
  currentSubmissionId,
  submissions,
}) => {
  if (!submissions || submissions.length <= 1) {
    return null
  }

  // Sort versions descending (v2, v1)
  const sorted = [...submissions].sort((a, b) => b.version_number - a.version_number)

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-state-success/15 px-2 py-0.5 text-[10px] font-semibold text-state-success">
            <CheckCircle2 className="h-2.5 w-2.5" aria-hidden="true" />
            Passed
          </span>
        )
      case 'CHANGES_REQUESTED':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-state-warning/15 px-2 py-0.5 text-[10px] font-semibold text-state-warning">
            <AlertTriangle className="h-2.5 w-2.5" aria-hidden="true" />
            Changes Requested
          </span>
        )
      case 'SUBMITTED':
      case 'UNDER_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-accent-cyan/15 px-2 py-0.5 text-[10px] font-semibold text-accent-cyan">
            <Clock className="h-2.5 w-2.5" aria-hidden="true" />
            In Review
          </span>
        )
      case 'DRAFT':
      default:
        return (
          <span className="rounded bg-bg-surface px-2 py-0.5 text-[10px] font-medium text-text-muted border border-border-subtle">
            Draft
          </span>
        )
    }
  }

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-4 sm:p-5">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <History className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
          <span>Revision History & Versions</span>
        </h4>
        <span className="text-xs text-text-muted font-mono">
          {submissions.length} revision{submissions.length === 1 ? '' : 's'} recorded
        </span>
      </div>

      <div className="space-y-2.5">
        {sorted.map((sub) => {
          const isCurrent = sub.id === currentSubmissionId

          return (
            <div
              key={sub.id}
              className={`flex items-center justify-between gap-3 rounded-lg border p-3 transition-colors ${
                isCurrent
                  ? 'border-accent-violet/40 bg-accent-violet/5 shadow-sm'
                  : 'border-border-subtle bg-bg-surface/30 hover:bg-bg-surface/60'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`rounded-full p-1.5 shrink-0 ${
                    isCurrent
                      ? 'bg-accent-violet text-white'
                      : 'bg-bg-surface text-text-muted border border-border-subtle'
                  }`}
                >
                  <GitCommit className="h-3.5 w-3.5" aria-hidden="true" />
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-text-primary">
                      Version {sub.version_number}
                    </span>
                    {isCurrent && (
                      <span className="rounded bg-accent-violet/20 px-1.5 py-0.2 text-[10px] font-medium text-accent-violet border border-accent-violet/30">
                        Active Workspace
                      </span>
                    )}
                    {getStatusBadge(sub.status)}
                  </div>

                  <div className="mt-0.5 flex items-center gap-2 text-[11px] text-text-muted font-mono">
                    <span>{new Date(sub.created_at).toLocaleDateString()}</span>
                    {sub.score !== null && sub.score !== undefined && (
                      <>
                        <span>&bull;</span>
                        <span>Score: {sub.score.toFixed(1)}/100</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {!isCurrent && (
                <Link
                  to={`/submissions/${sub.id}`}
                  className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-accent-cyan hover:text-accent-cyan-hover hover:bg-accent-cyan/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet"
                >
                  <span>Inspect</span>
                  <ArrowRight className="h-3 w-3" aria-hidden="true" />
                </Link>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

