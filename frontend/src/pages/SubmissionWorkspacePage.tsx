import React, { useEffect, useState, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  FolderGit2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Send,
  Save,
  Loader2,
  AlertCircle,
  GitBranch,
  FileText,
  Sparkles,
} from 'lucide-react'
import type {
  Artifact,
  ProjectDetail,
  SubmissionDetail,
  SubmissionHistoryResponse,
} from '../types/project'
import { projectApi } from '../services/projectApi'
import { MilestoneList } from '../features/projects/MilestoneList'
import { ArtifactManager } from '../features/projects/ArtifactManager'
import { EvaluationFeedback } from '../features/projects/EvaluationFeedback'
import { RevisionHistory } from '../features/projects/RevisionHistory'
import { ApiError } from '../services/api'

export const SubmissionWorkspacePage: React.FC = () => {
  const { submissionId } = useParams<{ submissionId: string }>()
  const navigate = useNavigate()

  const [submission, setSubmission] = useState<SubmissionDetail | null>(null)
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [history, setHistory] = useState<SubmissionHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Draft form states
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [demoUrl, setDemoUrl] = useState('')
  const [notes, setNotes] = useState('')
  const [completedMilestones, setCompletedMilestones] = useState<string[]>([])

  // Action states
  const [isSaving, setIsSaving] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isCreatingRevision, setIsCreatingRevision] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null)

  const loadSubmissionData = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const sub = await projectApi.getSubmission(id)
      setSubmission(sub)
      setTitle(sub.title || '')
      setSummary(sub.summary || '')
      setCompletedMilestones(sub.milestones_completed || [])

      const content = (sub.content as Record<string, unknown>) || {}
      setRepoUrl(typeof content.repo_url === 'string' ? content.repo_url : '')
      setDemoUrl(typeof content.demo_url === 'string' ? content.demo_url : '')
      setNotes(typeof content.notes === 'string' ? content.notes : '')

      // Load project specification
      const proj = await projectApi.getProject(sub.project_id)
      setProject(proj)

      // Load revision history
      try {
        const hist = await projectApi.getSubmissionHistory(id)
        setHistory(hist)
      } catch {
        // Revision history error is non-fatal
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load submission. Please verify access or try again.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (submissionId) {
      loadSubmissionData(submissionId)
    }
  }, [submissionId, loadSubmissionData])

  const isDraft = submission?.status === 'DRAFT'
  const isChangesRequested = submission?.status === 'CHANGES_REQUESTED'
  const isCompleted = submission?.status === 'COMPLETED'

  const handleToggleMilestone = (mId: string) => {
    if (!isDraft) return
    setCompletedMilestones((prev) =>
      prev.includes(mId) ? prev.filter((id) => id !== mId) : [...prev, mId]
    )
  }

  const handleSaveDraft = async () => {
    if (!submission || !isDraft) return
    setIsSaving(true)
    setActionError(null)
    setSaveSuccessMsg(null)

    try {
      const contentPayload: Record<string, unknown> = {
        ...(submission.content || {}),
        repo_url: repoUrl.trim() || undefined,
        demo_url: demoUrl.trim() || undefined,
        notes: notes.trim() || undefined,
      }

      const updated = await projectApi.updateDraftSubmission(submission.id, {
        title: title.trim() || undefined,
        summary: summary.trim() || undefined,
        content: contentPayload,
        milestones_completed: completedMilestones,
      })

      setSubmission(updated)
      setSaveSuccessMsg('Draft progress successfully saved.')
      setTimeout(() => setSaveSuccessMsg(null), 4000)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setActionError(err.message || 'Failed to save draft.')
      } else {
        setActionError('Failed to save draft.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleSubmit = async () => {
    if (!submission || !isDraft) return

    // Quick client-side check matching backend requirement:
    const hasSummary = summary.trim().length > 0
    const hasArtifacts = submission.artifacts && submission.artifacts.length > 0
    const hasUrls = repoUrl.trim().length > 0 || demoUrl.trim().length > 0 || notes.trim().length > 0

    if (!hasSummary && !hasArtifacts && !hasUrls) {
      setActionError(
        'Cannot submit an empty draft. Please provide summary notes, deliverables, repository/demo URLs, or uploaded artifacts.'
      )
      return
    }

    setIsSubmitting(true)
    setActionError(null)

    try {
      // 1. Auto-save current edits first
      const contentPayload: Record<string, unknown> = {
        ...(submission.content || {}),
        repo_url: repoUrl.trim() || undefined,
        demo_url: demoUrl.trim() || undefined,
        notes: notes.trim() || undefined,
      }

      await projectApi.updateDraftSubmission(submission.id, {
        title: title.trim() || undefined,
        summary: summary.trim() || undefined,
        content: contentPayload,
        milestones_completed: completedMilestones,
      })

      // 2. Submit for evaluation
      const submitted = await projectApi.submitProject(submission.id)
      setSubmission(submitted)

      // Refresh history to reflect updated status
      try {
        const hist = await projectApi.getSubmissionHistory(submission.id)
        setHistory(hist)
      } catch {
        // ignore
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setActionError(err.message || 'Submission failed. Please verify all requirements.')
      } else {
        setActionError('Submission failed. Please check your network connection.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateRevision = async () => {
    if (!submission || !isChangesRequested) return
    setIsCreatingRevision(true)
    setActionError(null)

    try {
      const newRev = await projectApi.createRevision(submission.id)
      navigate(`/submissions/${newRev.id}`)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setActionError(err.message || 'Failed to create revision draft.')
      } else {
        setActionError('Failed to create revision draft.')
      }
      setIsCreatingRevision(false)
    }
  }

  const handleArtifactsChange = (newArtifacts: Artifact[]) => {
    if (!submission) return
    setSubmission({
      ...submission,
      artifacts: newArtifacts,
    })
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-accent-violet" aria-hidden="true" />
        <p className="text-sm text-text-muted">Loading submission workspace...</p>
      </main>
    )
  }

  if (error || !submission) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto text-center space-y-5">
        <div className="inline-flex rounded-full bg-state-error/10 p-4 text-state-error">
          <AlertCircle className="h-8 w-8" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-bold text-text-primary">Submission Workspace Unavailable</h1>
        <p className="text-sm text-text-secondary max-w-md mx-auto">{error}</p>
        <Link
          to="/projects"
          className="inline-flex items-center gap-2 rounded-lg bg-bg-surface border border-border-subtle px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-elevated transition-colors"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          <span>Back to Projects</span>
        </Link>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-bg-base py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Navigation Breadcrumbs */}
      <div className="flex items-center justify-between">
        <Link
          to={project ? `/projects/${project.slug || project.id}` : '/projects'}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-accent-cyan transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet px-1 py-0.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Back to {project?.title || 'Project Details'}</span>
        </Link>

        <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
          <span>Submission ID:</span>
          <span className="text-text-secondary font-semibold">{submission.id.slice(0, 8)}...</span>
        </div>
      </div>

      {/* Status Hero Card */}
      <div className="rounded-2xl border border-border-subtle bg-bg-elevated/70 p-6 sm:p-8 backdrop-blur-md space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="rounded-md bg-accent-violet/15 px-2.5 py-1 text-xs font-bold text-accent-violet border border-accent-violet/30">
              Version {submission.version_number}
            </span>

            {/* Lifecycle Status Pill */}
            {submission.status === 'COMPLETED' && (
              <span className="inline-flex items-center gap-1.5 rounded-md bg-state-success/15 px-3 py-1 text-xs font-bold text-state-success border border-state-success/30">
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                Passed & Completed
              </span>
            )}
            {submission.status === 'CHANGES_REQUESTED' && (
              <span className="inline-flex items-center gap-1.5 rounded-md bg-state-warning/15 px-3 py-1 text-xs font-bold text-state-warning border border-state-warning/30">
                <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                Changes Requested
              </span>
            )}
            {(submission.status === 'SUBMITTED' || submission.status === 'UNDER_REVIEW') && (
              <span className="inline-flex items-center gap-1.5 rounded-md bg-accent-cyan/15 px-3 py-1 text-xs font-bold text-accent-cyan border border-accent-cyan/30">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                {submission.status === 'UNDER_REVIEW' ? 'Under Review' : 'Submitted for Evaluation'}
              </span>
            )}
            {submission.status === 'EVALUATED' && (
              <span className="inline-flex items-center gap-1.5 rounded-md bg-accent-violet/15 px-3 py-1 text-xs font-bold text-accent-violet border border-accent-violet/30">
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                Evaluated
              </span>
            )}
            {submission.status === 'DRAFT' && (
              <span className="rounded-md bg-bg-surface px-3 py-1 text-xs font-medium text-text-secondary border border-border-subtle">
                Draft In Progress
              </span>
            )}
          </div>

          <div className="text-xs text-text-muted font-mono">
            Created: {new Date(submission.created_at).toLocaleDateString()}
            {submission.submitted_at && (
              <span> &bull; Submitted: {new Date(submission.submitted_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>

        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-text-primary">
            {project?.title || submission.title || 'Project Submission'}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-text-secondary">
            {isDraft
              ? 'Complete your project deliverables, check off finished milestones, and attach required artifacts before submitting for evaluation.'
              : isChangesRequested
              ? 'The reviewer evaluated your submission and requested adjustments. Review the feedback below and launch a new revision.'
              : isCompleted
              ? 'Congratulations! This practical capstone has been evaluated and accepted toward your demonstrated skill mastery.'
              : 'Your deliverables are currently awaiting review by an instructor against the published evaluation rubric.'}
          </p>
        </div>

        {/* Changes Requested Banner */}
        {isChangesRequested && (
          <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-state-warning/30 bg-state-warning/10 p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-state-warning shrink-0 mt-0.5" aria-hidden="true" />
              <div className="text-xs text-state-warning leading-relaxed">
                <strong className="font-semibold">Revision Required:</strong> You can initiate a new immutable revision draft based on this version while preserving the reviewer's feedback.
              </div>
            </div>

            <button
              type="button"
              onClick={handleCreateRevision}
              disabled={isCreatingRevision}
              className="inline-flex items-center gap-2 rounded-lg bg-state-warning px-4 py-2 text-xs font-semibold text-bg-base hover:bg-state-warning/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-state-warning cursor-pointer shrink-0 disabled:opacity-50"
            >
              {isCreatingRevision ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  <span>Creating Revision...</span>
                </>
              ) : (
                <>
                  <GitBranch className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Start Revision Draft</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Action / Error Banners */}
      {actionError && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-xl border border-state-error/30 bg-state-error/10 p-4 text-xs text-state-error"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1 leading-relaxed">
            <strong>Action Error:</strong> {actionError}
          </div>
        </div>
      )}

      {saveSuccessMsg && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-xl border border-state-success/30 bg-state-success/10 p-4 text-xs text-state-success"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Evaluation Results Component (if evaluated) */}
      {submission.evaluation && (
        <section aria-labelledby="section-evaluation" className="space-y-3">
          <h2 id="section-evaluation" className="text-base font-bold text-text-primary">
            Evaluator Assessment & Scoring
          </h2>
          <EvaluationFeedback
            evaluation={submission.evaluation}
            rubricCriteria={project?.evaluation_criteria?.rubric}
            evaluatorName={submission.evaluator_name}
            evaluatedAt={submission.evaluated_at}
            status={submission.status}
          />
        </section>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Form Inputs (Title, Summary, URLs) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deliverables / Submission Form */}
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 sm:p-6 space-y-5">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
              <span>Project Deliverables & Notes</span>
            </h3>

            {/* Submission Title */}
            <div>
              <label htmlFor="sub-title" className="block text-xs font-medium text-text-secondary mb-1">
                Submission Title
              </label>
              <input
                id="sub-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={!isDraft}
                placeholder="e.g. Scalable Inventory API Service v1"
                className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet disabled:opacity-60 transition-colors"
              />
            </div>

            {/* Summary & Implementation Approach */}
            <div>
              <label htmlFor="sub-summary" className="block text-xs font-medium text-text-secondary mb-1">
                Summary & Approach Notes
              </label>
              <textarea
                id="sub-summary"
                rows={4}
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                disabled={!isDraft}
                placeholder="Describe your implementation architecture, key design decisions, trade-offs made, and instructions for running the project..."
                className="w-full rounded-lg border border-border-subtle bg-bg-surface p-3 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet disabled:opacity-60 transition-colors resize-y leading-relaxed"
              />
            </div>

            {/* URLs Grid (Repository & Live Demo) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="sub-repo-url" className="block text-xs font-medium text-text-secondary mb-1">
                  Repository URL (GitHub / GitLab)
                </label>
                <input
                  id="sub-repo-url"
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  disabled={!isDraft}
                  placeholder="https://github.com/username/project"
                  className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet disabled:opacity-60 transition-colors"
                />
              </div>

              <div>
                <label htmlFor="sub-demo-url" className="block text-xs font-medium text-text-secondary mb-1">
                  Live Deployment / Demo URL
                </label>
                <input
                  id="sub-demo-url"
                  type="url"
                  value={demoUrl}
                  onChange={(e) => setDemoUrl(e.target.value)}
                  disabled={!isDraft}
                  placeholder="https://demo.example.com"
                  className="w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet disabled:opacity-60 transition-colors"
                />
              </div>
            </div>

            {/* Additional Technical Notes */}
            <div>
              <label htmlFor="sub-notes" className="block text-xs font-medium text-text-secondary mb-1">
                Additional Technical Notes (Optional)
              </label>
              <textarea
                id="sub-notes"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={!isDraft}
                placeholder="Any special configuration instructions, test accounts, or environment variables needed by the reviewer..."
                className="w-full rounded-lg border border-border-subtle bg-bg-surface p-3 text-sm text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none focus:ring-1 focus:ring-accent-violet disabled:opacity-60 transition-colors resize-y leading-relaxed"
              />
            </div>

            {/* Actions: Save Draft and Submit */}
            {isDraft && (
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle">
                <button
                  type="button"
                  onClick={handleSaveDraft}
                  disabled={isSaving || isSubmitting}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-4 py-2 text-xs font-semibold text-text-primary hover:bg-bg-elevated transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer disabled:opacity-50"
                >
                  {isSaving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Save className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  <span>Save Draft</span>
                </button>

                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSaving || isSubmitting}
                  className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-5 py-2 text-xs font-semibold text-white shadow-md hover:bg-accent-violet-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                      <span>Submitting Deliverables...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Submit for Evaluation</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Artifact Manager Component */}
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 sm:p-6 space-y-4">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <FolderGit2 className="h-4 w-4 text-accent-violet" aria-hidden="true" />
              <span>Deliverable Artifact Files</span>
            </h3>

            <ArtifactManager
              submissionId={submission.id}
              artifacts={submission.artifacts || []}
              isDraft={isDraft}
              onArtifactsChange={handleArtifactsChange}
            />
          </div>
        </div>

        {/* Right Column: Milestones Checklist & Revision History */}
        <div className="space-y-6">
          {/* Milestones Checklist */}
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 space-y-4">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Project Milestones
            </h3>
            <MilestoneList
              milestones={project?.requirements?.milestones || []}
              completedIds={completedMilestones}
              isInteractive={isDraft}
              onToggleMilestone={handleToggleMilestone}
            />
          </div>

          {/* Revision History Component */}
          {history && history.submissions && history.submissions.length > 1 && (
            <RevisionHistory
              currentSubmissionId={submission.id}
              submissions={history.submissions}
            />
          )}

          {/* Project Rubric Reference (Accordion or Compact View) */}
          {project?.evaluation_criteria?.rubric && (
            <div className="rounded-xl border border-border-subtle bg-bg-surface/30 p-4 space-y-3">
              <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                Rubric Passing Standard
              </h4>
              <div className="text-xs text-text-muted space-y-1.5">
                <div className="flex justify-between">
                  <span>Passing Score Required:</span>
                  <span className="font-mono font-bold text-text-primary">
                    {project.evaluation_criteria.passing_score ?? 70}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Evaluation Rubric Criteria:</span>
                  <span className="font-mono text-text-secondary">
                    {project.evaluation_criteria.rubric.length} criteria
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
