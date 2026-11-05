import React, { useMemo } from 'react'
import {
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Circle,
  FileCode,
  AlertTriangle,
  BookOpen,
} from 'lucide-react'
import type { MilestoneItem, WebPracticeSubmission } from '../../types/activity'

interface WebPracticeActivityProps {
  problemStatement?: string
  learningObjectives?: string[]
  milestones?: MilestoneItem[]
  requireRepoUrl?: boolean
  requireLiveUrl?: boolean
  requireReflection?: boolean
  submission: Partial<WebPracticeSubmission>
  onChange: (updated: Partial<WebPracticeSubmission>) => void
  disabled?: boolean
}

const SAFE_URL_REGEX = /^https?:\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+$/

function isValidUrl(val: string): boolean {
  if (!val || !val.trim()) return false
  const trimmed = val.trim()
  if (!SAFE_URL_REGEX.test(trimmed)) return false
  try {
    const parsed = new URL(trimmed)
    return (
      (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      parsed.hostname.includes('.')
    )
  } catch {
    return false
  }
}

export const WebPracticeActivity: React.FC<WebPracticeActivityProps> = ({
  problemStatement,
  learningObjectives = [],
  milestones = [],
  requireRepoUrl = true,
  requireLiveUrl = false,
  requireReflection = true,
  submission,
  onChange,
  disabled = false,
}) => {
  const repoUrl = submission.repo_url || ''
  const liveUrl = submission.live_url || ''
  const notes = submission.implementation_notes || ''
  const completedIds = submission.completed_milestone_ids || []
  const reflection = submission.reflection || ''

  // Real-time URL format validation warnings
  const repoUrlWarning = useMemo(() => {
    if (!repoUrl.trim()) return null
    return isValidUrl(repoUrl)
      ? null
      : 'Must be a valid HTTP or HTTPS repository URL (e.g., https://github.com/org/repo).'
  }, [repoUrl])

  const liveUrlWarning = useMemo(() => {
    if (!liveUrl.trim()) return null
    return isValidUrl(liveUrl)
      ? null
      : 'Must be a valid HTTP or HTTPS demonstration URL (e.g., https://example.com).'
  }, [liveUrl])

  // Word count for reflection
  const reflectionWordCount = useMemo(() => {
    return reflection.trim() ? reflection.trim().split(/\s+/).length : 0
  }, [reflection])

  const toggleMilestone = (id: string) => {
    if (disabled) return
    const updated = completedIds.includes(id)
      ? completedIds.filter((item) => item !== id)
      : [...completedIds, id]
    onChange({ ...submission, completed_milestone_ids: updated })
  }

  return (
    <div className="space-y-6 my-4 font-sans text-text-primary">
      {/* 1. Problem Statement & Context */}
      {problemStatement && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-accent-cyan">
            <FileCode className="w-4 h-4" />
            <span>Problem Statement & Brief</span>
          </div>
          <p className="text-sm text-text-primary leading-relaxed whitespace-pre-line">
            {problemStatement}
          </p>
        </div>
      )}

      {/* 2. Learning Objectives */}
      {learningObjectives.length > 0 && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-accent-violet">
            <BookOpen className="w-4 h-4" />
            <span>Learning Objectives</span>
          </div>
          <ul className="space-y-1.5 text-sm text-text-secondary">
            {learningObjectives.map((obj, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-violet mt-2 shrink-0" />
                <span>{obj}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 3. Interactive Milestone Checklist */}
      {milestones.length > 0 && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-text-muted">
              Implementation Milestones ({completedIds.length}/{milestones.length} Completed)
            </span>
            <span className="text-xs text-text-muted font-mono">Check off as you build</span>
          </div>

          <div role="group" aria-label="Milestones checklist" className="space-y-2">
            {milestones.map((m) => {
              const isChecked = completedIds.includes(m.id)
              return (
                <button
                  type="button"
                  key={m.id}
                  disabled={disabled}
                  onClick={() => toggleMilestone(m.id)}
                  aria-pressed={isChecked}
                  className={`w-full text-left p-3 rounded-lg border transition-all flex items-start gap-3 cursor-pointer ${
                    isChecked
                      ? 'bg-accent-emerald/10 border-accent-emerald/30 text-text-primary'
                      : 'bg-bg-elevated border-border-subtle hover:border-border-medium text-text-secondary'
                  } ${disabled ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  <div className="mt-0.5 shrink-0">
                    {isChecked ? (
                      <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
                    ) : (
                      <Circle className="w-4 h-4 text-text-muted" />
                    )}
                  </div>
                  <div className="flex-1 space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{m.title}</span>
                      {m.required !== false ? (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-violet/10 text-accent-violet border border-accent-violet/20">
                          Required
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-bg-surface text-text-muted border border-border-subtle">
                          Optional
                        </span>
                      )}
                    </div>
                    {m.description && (
                      <p className="text-xs text-text-muted leading-relaxed">{m.description}</p>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* 4. Deliverables Inputs */}
      <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-4">
        <span className="text-xs font-mono uppercase tracking-wider text-text-muted block">
          Practice Deliverables
        </span>

        {/* Repository URL */}
        <div className="space-y-1.5">
          <label htmlFor="web-repo-url" className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
            <span>Repository URL</span>
            {requireRepoUrl ? (
              <span className="text-accent-violet font-mono text-[10px]">*Required</span>
            ) : (
              <span className="text-text-muted font-mono text-[10px]">(Optional)</span>
            )}
          </label>
          <div className="relative">
            <input
              id="web-repo-url"
              type="url"
              disabled={disabled}
              value={repoUrl}
              onChange={(e) => onChange({ ...submission, repo_url: e.target.value })}
              placeholder="https://github.com/your-username/your-repo"
              className={`w-full px-3 py-2 rounded-lg bg-bg-elevated border text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:ring-1 transition-all ${
                repoUrlWarning
                  ? 'border-state-error/60 focus:border-state-error focus:ring-state-error'
                  : 'border-border-medium focus:border-accent-violet focus:ring-accent-violet'
              }`}
            />
            {repoUrl && isValidUrl(repoUrl) && (
              <a
                href={repoUrl}
                target="_blank"
                rel="noreferrer noopener"
                className="absolute right-2.5 top-2.5 text-text-muted hover:text-text-primary"
                title="Preview external URL in new tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
          {repoUrlWarning && (
            <p className="text-xs text-state-error flex items-center gap-1.5 mt-1" role="alert">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>{repoUrlWarning}</span>
            </p>
          )}
        </div>

        {/* Live Demonstration URL */}
        <div className="space-y-1.5">
          <label htmlFor="web-live-url" className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
            <span>Live Demonstration URL</span>
            {requireLiveUrl ? (
              <span className="text-accent-violet font-mono text-[10px]">*Required</span>
            ) : (
              <span className="text-text-muted font-mono text-[10px]">(Optional)</span>
            )}
          </label>
          <div className="relative">
            <input
              id="web-live-url"
              type="url"
              disabled={disabled}
              value={liveUrl}
              onChange={(e) => onChange({ ...submission, live_url: e.target.value })}
              placeholder="https://your-preview-deployment.app"
              className={`w-full px-3 py-2 rounded-lg bg-bg-elevated border text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:ring-1 transition-all ${
                liveUrlWarning
                  ? 'border-state-error/60 focus:border-state-error focus:ring-state-error'
                  : 'border-border-medium focus:border-accent-violet focus:ring-accent-violet'
              }`}
            />
            {liveUrl && isValidUrl(liveUrl) && (
              <a
                href={liveUrl}
                target="_blank"
                rel="noreferrer noopener"
                className="absolute right-2.5 top-2.5 text-text-muted hover:text-text-primary"
                title="Preview demonstration URL in new tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
          {liveUrlWarning && (
            <p className="text-xs text-state-error flex items-center gap-1.5 mt-1" role="alert">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>{liveUrlWarning}</span>
            </p>
          )}
        </div>

        {/* Implementation Notes */}
        <div className="space-y-1.5">
          <label htmlFor="web-notes" className="text-xs font-semibold text-text-secondary block">
            Implementation Notes & Tech Stack (Optional)
          </label>
          <textarea
            id="web-notes"
            rows={2}
            disabled={disabled}
            value={notes}
            onChange={(e) => onChange({ ...submission, implementation_notes: e.target.value })}
            placeholder="Highlight architecture, libraries, or responsive design choices..."
            className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet transition-all"
          />
        </div>

        {/* Technical Reflection */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="web-reflection" className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
              <span>Technical Reflection</span>
              {requireReflection && <span className="text-accent-violet font-mono text-[10px]">*Required</span>}
            </label>
            <span
              className={`text-xs font-mono ${
                requireReflection && reflectionWordCount < 10
                  ? 'text-accent-amber'
                  : 'text-text-muted'
              }`}
            >
              {reflectionWordCount} words {requireReflection && '(min 10 words)'}
            </span>
          </div>
          <textarea
            id="web-reflection"
            rows={3}
            disabled={disabled}
            value={reflection}
            onChange={(e) => onChange({ ...submission, reflection: e.target.value })}
            placeholder="What technical challenges did you encounter, and how did you resolve them?"
            className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet transition-all"
          />
        </div>
      </div>

      {/* 5. Security & Evaluation Notice */}
      <div className="p-3.5 rounded-xl bg-bg-surface border border-accent-cyan/20 flex items-start gap-2.5 text-xs text-text-muted leading-relaxed">
        <ShieldCheck className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-text-secondary">Safe Rubric Evaluation: </span>
          SkillVerse deterministically evaluates deliverable syntax, milestone completion, and reflections
          against rubric criteria on the server. External URLs are validated for safe protocols but are
          never executed automatically in host environments.
        </div>
      </div>
    </div>
  )
}
