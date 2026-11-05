import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Clock,
  Sparkles,
  BookOpen,
  FolderGit2,
  ExternalLink,
  AlertCircle,
  Loader2,
  FileText,
  Play,
} from 'lucide-react'
import type { ProjectDetail } from '../types/project'
import { projectApi } from '../services/projectApi'
import { useAuth } from '../context/AuthContext'
import { MilestoneList } from '../features/projects/MilestoneList'
import { RubricView } from '../features/projects/RubricView'
import { Badge } from '../components/ui/Badge'

export const ProjectDetailPage: React.FC = () => {
  const { slugOrId } = useParams<{ slugOrId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)

  useEffect(() => {
    if (!slugOrId) return
    let mounted = true
    setLoading(true)
    setError(null)

    projectApi
      .getProject(slugOrId)
      .then((res) => {
        if (mounted) setProject(res)
      })
      .catch((err: unknown) => {
        if (mounted) {
          setError(
            err instanceof Error ? err.message : 'Project not found or temporarily unavailable.'
          )
        }
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [slugOrId])

  const handleStartProject = async () => {
    if (!project) return
    if (!user) {
      navigate(`/login?redirect=/projects/${project.slug || project.id}`)
      return
    }

    try {
      setStarting(true)
      setStartError(null)
      const submission = await projectApi.startOrGetSubmission(project.id)
      navigate(`/submissions/${submission.id}`)
    } catch (err: unknown) {
      setStartError(
        err instanceof Error ? err.message : 'Failed to start project draft. Please try again.'
      )
    } finally {
      setStarting(false)
    }
  }

  const getDifficultyBadge = (level: string) => {
    switch (level) {
      case 'BEGINNER':
        return <Badge variant="emerald">Beginner</Badge>
      case 'INTERMEDIATE':
        return <Badge variant="cyan">Intermediate</Badge>
      case 'ADVANCED':
        return <Badge variant="violet">Advanced</Badge>
      case 'EXPERT':
        return <Badge variant="amber">Expert</Badge>
      default:
        return <Badge variant="default">{level}</Badge>
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="rounded bg-state-success/20 px-2 py-0.5 text-xs font-semibold text-state-success">Completed & Passed</span>
      case 'CHANGES_REQUESTED':
        return <span className="rounded bg-state-warning/20 px-2 py-0.5 text-xs font-semibold text-state-warning">Changes Requested</span>
      case 'SUBMITTED':
      case 'UNDER_REVIEW':
        return <span className="rounded bg-accent-cyan/20 px-2 py-0.5 text-xs font-semibold text-accent-cyan">Under Evaluation</span>
      case 'DRAFT':
      default:
        return <span className="rounded bg-bg-surface px-2 py-0.5 text-xs font-medium text-text-secondary border border-border-subtle">Draft In Progress</span>
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-accent-cyan" aria-hidden="true" />
        <p className="text-sm text-text-muted">Loading project specification and rubric...</p>
      </main>
    )
  }

  if (error || !project) {
    return (
      <main className="min-h-screen bg-bg-base py-12 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto text-center space-y-5">
        <div className="inline-flex rounded-full bg-state-error/10 p-4 text-state-error">
          <AlertCircle className="h-8 w-8" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-bold text-text-primary">Project Specification Not Found</h1>
        <p className="text-sm text-text-secondary max-w-md mx-auto">
          {error || "The requested practical project could not be found or has not been published yet."}
        </p>
        <Link
          to="/projects"
          className="inline-flex items-center gap-2 rounded-lg bg-bg-surface border border-border-subtle px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-elevated transition-colors"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          <span>Back to Projects Catalog</span>
        </Link>
      </main>
    )
  }

  const deliverables = project.requirements?.deliverables || []
  const milestones = project.requirements?.milestones || []
  const guidelines = project.requirements?.guidelines

  return (
    <main className="min-h-screen bg-bg-base py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Back Link */}
      <div>
        <Link
          to="/projects"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-accent-cyan transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet px-1 py-0.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Back to Projects Catalog</span>
        </Link>
      </div>

      {/* Hero Header Card */}
      <div className="rounded-2xl border border-border-subtle bg-bg-elevated/70 p-6 sm:p-8 backdrop-blur-md space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {project.discipline_name && (
              <span className="rounded-md bg-bg-surface px-2.5 py-1 text-xs font-medium text-text-secondary border border-border-subtle">
                {project.discipline_name}
              </span>
            )}
            {getDifficultyBadge(project.difficulty_level)}
          </div>

          {project.estimated_duration_hours && (
            <div className="flex items-center gap-1.5 text-xs text-text-muted font-mono">
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Estimated: {project.estimated_duration_hours} hours</span>
            </div>
          )}
        </div>

        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text-primary">
            {project.title}
          </h1>
          <p className="mt-2 text-base text-text-secondary leading-relaxed">
            {project.short_description}
          </p>
        </div>

        {/* Demonstrated Skills */}
        {project.skills && project.skills.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border-subtle/50">
            <span className="text-xs text-text-muted mr-1">Skills Demonstrated:</span>
            {project.skills.map((s) => (
              <span
                key={s.skill_id}
                className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium border ${
                  s.is_primary
                    ? 'border-accent-violet/30 bg-accent-violet/10 text-accent-violet'
                    : 'border-border-subtle bg-bg-surface text-text-secondary'
                }`}
              >
                {s.is_primary && <Sparkles className="h-3 w-3" aria-hidden="true" />}
                {s.skill_name}
              </span>
            ))}
          </div>
        )}

        {/* Start / Continue Action Callout */}
        <div className="rounded-xl border border-border-subtle bg-bg-surface/60 p-4 sm:p-5 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Learner Progress & Status
            </div>
            {project.my_submission ? (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary">
                  Version {project.my_submission.version_number}:
                </span>
                {getStatusBadge(project.my_submission.status)}
              </div>
            ) : (
              <div className="text-sm text-text-secondary">
                Ready to begin? Start your draft submission workspace to track milestones and attach deliverables.
              </div>
            )}
          </div>

          <div>
            {startError && (
              <div role="alert" className="text-xs text-state-error mb-2">
                {startError}
              </div>
            )}

            {project.my_submission ? (
              <Link
                to={`/submissions/${project.my_submission.id}`}
                className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-lg bg-accent-violet px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-accent-violet-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
              >
                <span>Continue in Workspace</span>
                <FolderGit2 className="h-4 w-4" aria-hidden="true" />
              </Link>
            ) : (
              <button
                type="button"
                onClick={handleStartProject}
                disabled={starting}
                className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-lg bg-accent-cyan px-5 py-2.5 text-sm font-semibold text-bg-base hover:bg-accent-cyan-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan cursor-pointer disabled:opacity-50"
              >
                {starting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    <span>Preparing Workspace...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-current" aria-hidden="true" />
                    <span>Start Project</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Description, Deliverables, Milestones, Rubric */}
      <div className="space-y-8">
        {/* Full Project Description */}
        <section aria-labelledby="section-overview" className="space-y-3">
          <h2 id="section-overview" className="text-lg font-bold text-text-primary flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-accent-cyan" aria-hidden="true" />
            <span>Project Scope & Context</span>
          </h2>
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 sm:p-6 text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
            {project.full_description}
          </div>
        </section>

        {/* Milestones and Deliverables Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Milestones Checklist */}
          <section aria-labelledby="section-milestones" className="space-y-3">
            <h2 id="section-milestones" className="text-lg font-bold text-text-primary">
              Project Milestones
            </h2>
            <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5">
              <MilestoneList
                milestones={milestones}
                completedIds={project.my_submission ? [] : []}
                isInteractive={false}
              />
            </div>
          </section>

          {/* Expected Deliverables */}
          <section aria-labelledby="section-deliverables" className="space-y-3">
            <h2 id="section-deliverables" className="text-lg font-bold text-text-primary">
              Expected Deliverables
            </h2>
            <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 space-y-3">
              {deliverables.length > 0 ? (
                <ul className="space-y-2.5" aria-label="Expected deliverables">
                  {deliverables.map((item, idx) => {
                    const text = typeof item === 'string' ? item : item.title
                    const desc = typeof item === 'string' ? undefined : item.description
                    return (
                      <li key={idx} className="flex items-start gap-2.5 text-sm text-text-secondary">
                        <FileText className="h-4 w-4 text-accent-violet shrink-0 mt-0.5" aria-hidden="true" />
                        <div>
                          <strong className="text-text-primary font-medium">{text}</strong>
                          {desc && <p className="text-xs text-text-muted mt-0.5">{desc}</p>}
                        </div>
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <p className="text-xs text-text-muted">
                  Follow the guidelines outlined in the project scope.
                </p>
              )}

              {/* Guidelines if present */}
              {guidelines && (
                <div className="mt-4 rounded-lg border border-border-subtle bg-bg-surface/30 p-3 text-xs text-text-secondary leading-relaxed">
                  <div className="font-semibold text-text-primary mb-1">Author Guidelines:</div>
                  {Array.isArray(guidelines) ? (
                    <ul className="list-disc list-inside space-y-1">
                      {guidelines.map((g, idx) => (
                        <li key={idx}>{g}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>{guidelines}</p>
                  )}
                </div>
              )}

              {/* Artifact Limits Summary */}
              <div className="mt-4 rounded-lg border border-border-subtle bg-bg-surface/50 p-3 text-xs text-text-muted space-y-1">
                <div className="font-semibold text-text-secondary">Upload Guidelines:</div>
                <div>&bull; Formats: ZIP, TAR.GZ, PDF, PNG, JPG, WEBP, TXT, MD, JSON, CSV</div>
                <div>&bull; Limit: Up to 10 files (20 MB single / 50 MB total aggregate)</div>
                <div>&bull; Security: Active script files (.exe, .py, .js) must be packed inside an archive</div>
              </div>
            </div>
          </section>
        </div>

        {/* Evaluation Rubric Section */}
        <section aria-labelledby="section-rubric" className="space-y-3">
          <h2 id="section-rubric" className="text-lg font-bold text-text-primary">
            Evaluation Criteria & Rubric
          </h2>
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5 sm:p-6">
            <RubricView criteria={project.evaluation_criteria} />
          </div>
        </section>

        {/* Starter Resources Section (if present) */}
        {project.starter_resources && project.starter_resources.length > 0 && (
          <section aria-labelledby="section-resources" className="space-y-3">
            <h2 id="section-resources" className="text-lg font-bold text-text-primary">
              Starter Templates & Reference Resources
            </h2>
            <div className="rounded-xl border border-border-subtle bg-bg-elevated/50 p-5">
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3" aria-label="Starter resources">
                {project.starter_resources.map((res, idx) => (
                  <li key={idx}>
                    <a
                      href={res.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start justify-between gap-3 rounded-lg border border-border-subtle bg-bg-surface/50 p-3.5 hover:bg-bg-surface hover:border-accent-cyan/40 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet"
                    >
                      <div>
                        <div className="text-sm font-medium text-text-primary group-hover:text-accent-cyan transition-colors">
                          {res.title}
                        </div>
                        {res.description && (
                          <div className="mt-1 text-xs text-text-muted">{res.description}</div>
                        )}
                      </div>
                      <ExternalLink className="h-4 w-4 text-text-muted group-hover:text-accent-cyan shrink-0 transition-colors mt-0.5" aria-hidden="true" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </div>
    </main>
  )
}
