import React from 'react'
import { Link } from 'react-router-dom'
import { Clock, Users, ArrowRight, Sparkles } from 'lucide-react'
import type { ProjectSummary } from '../../types/project'
import { Badge } from '../../components/ui/Badge'

interface ProjectCardProps {
  project: ProjectSummary
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project }) => {
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

  const primarySkill = project.skills.find((s) => s.is_primary)
  const secondarySkills = project.skills.filter((s) => !s.is_primary).slice(0, 3)

  return (
    <article
      aria-labelledby={`project-title-${project.id}`}
      className="group relative flex flex-col justify-between rounded-xl border border-border-subtle bg-bg-elevated/70 p-6 shadow-sm backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-border-medium hover:shadow-lg hover:shadow-accent-violet/5"
    >
      <div>
        {/* Header badges: Discipline & Difficulty */}
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {project.discipline_name && (
              <span className="rounded-md bg-bg-surface px-2.5 py-0.5 text-xs font-medium text-text-secondary">
                {project.discipline_name}
              </span>
            )}
            {getDifficultyBadge(project.difficulty_level)}
          </div>

          {project.estimated_duration_hours && (
            <div className="flex items-center gap-1.5 text-xs text-text-muted">
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{project.estimated_duration_hours}h est.</span>
            </div>
          )}
        </div>

        {/* Project Title */}
        <h2
          id={`project-title-${project.id}`}
          className="text-lg font-semibold tracking-tight text-text-primary transition-colors group-hover:text-accent-cyan"
        >
          <Link
            to={`/projects/${project.slug || project.id}`}
            className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet rounded"
          >
            {project.title}
          </Link>
        </h2>

        {/* Description */}
        <p className="mt-2 line-clamp-3 text-sm text-text-secondary leading-relaxed">
          {project.short_description}
        </p>

        {/* Skills Demonstrated */}
        {project.skills.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            {primarySkill && (
              <span
                key={primarySkill.skill_id}
                className="inline-flex items-center gap-1 rounded-md bg-accent-violet/10 px-2 py-0.5 text-xs font-medium text-accent-violet border border-accent-violet/20"
                title="Primary Focus Skill"
              >
                <Sparkles className="h-3 w-3" aria-hidden="true" />
                {primarySkill.skill_name}
              </span>
            )}
            {secondarySkills.map((s) => (
              <span
                key={s.skill_id}
                className="rounded-md bg-bg-surface px-2 py-0.5 text-xs text-text-muted border border-border-subtle"
              >
                {s.skill_name}
              </span>
            ))}
            {project.skills.length > 4 && (
              <span className="text-xs text-text-muted self-center">
                +{project.skills.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer / Action */}
      <div className="mt-6 flex items-center justify-between border-t border-border-subtle pt-4">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Users className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{project.submissions_count} submissions</span>
        </div>

        <Link
          to={`/projects/${project.slug || project.id}`}
          className="inline-flex items-center gap-1 text-xs font-medium text-accent-cyan transition-colors hover:text-accent-cyan-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet rounded px-1.5 py-0.5"
          aria-label={`View details for ${project.title}`}
        >
          <span>View Project</span>
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </Link>
      </div>
    </article>
  )
}
