import React from 'react'
import {
  Sparkles,
  ShieldCheck,
  Code2,
  Globe,
  Link as LinkIcon,
  Share2,
  Calendar,
  FolderGit2,
} from 'lucide-react'
import type { PortfolioPublic } from '../../types/portfolio'
import { PortfolioItemCard } from './PortfolioItemCard'

interface PublicPortfolioShowcaseProps {
  portfolio: PortfolioPublic
}

export const PublicPortfolioShowcase: React.FC<PublicPortfolioShowcaseProps> = ({
  portfolio,
}) => {
  // Aggregate all unique skills demonstrated across public items
  const allSkills = Array.from(
    new Set(portfolio.items.flatMap((item) => item.skills_demonstrated || []))
  )

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .filter(Boolean)
      .slice(0, 2)
      .join('')
      .toUpperCase() || 'SV'
  }

  return (
    <div className="space-y-10" aria-label={`Public Portfolio of ${portfolio.display_name}`}>
      {/* Hero Showcase Header */}
      <header className="relative overflow-hidden rounded-3xl border border-border-subtle bg-gradient-to-br from-bg-elevated via-bg-surface to-bg-elevated p-6 sm:p-8 md:p-10 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center gap-6 justify-between">
          <div className="flex items-start sm:items-center gap-5">
            {/* Avatar / Initials */}
            <div className="relative shrink-0">
              {portfolio.avatar_url ? (
                <img
                  src={portfolio.avatar_url}
                  alt={portfolio.display_name}
                  className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl object-cover border-2 border-accent-violet/40 shadow-lg"
                />
              ) : (
                <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white text-2xl font-extrabold shadow-lg shadow-accent-violet/20 border-2 border-border-subtle">
                  {getInitials(portfolio.display_name)}
                </div>
              )}
              <div
                className="absolute -bottom-1 -right-1 rounded-full bg-bg-base p-1 border border-border-subtle shadow"
                title="Verified SkillVerse Learner"
              >
                <ShieldCheck className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
              </div>
            </div>

            <div className="space-y-1.5 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text-primary">
                  {portfolio.display_name}
                </h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-accent-cyan/10 border border-accent-cyan/20 px-2 py-0.5 text-[10px] font-semibold text-accent-cyan">
                  <Sparkles className="h-2.5 w-2.5" aria-hidden="true" />
                  <span>Verified Learner</span>
                </span>
              </div>

              {portfolio.headline && (
                <p className="text-sm sm:text-base font-medium text-accent-violet leading-relaxed">
                  {portfolio.headline}
                </p>
              )}

              {portfolio.title && (
                <p className="text-xs text-text-muted font-mono">
                  {portfolio.title}
                </p>
              )}
            </div>
          </div>

          {/* Social / Contact Links */}
          {portfolio.contact_links && (
            <div className="flex flex-wrap items-center gap-2 pt-2 md:pt-0">
              {portfolio.contact_links.github && (
                <a
                  href={portfolio.contact_links.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
                  aria-label="GitHub Profile"
                >
                  <Code2 className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>GitHub</span>
                </a>
              )}
              {portfolio.contact_links.linkedin && (
                <a
                  href={portfolio.contact_links.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
                  aria-label="LinkedIn Profile"
                >
                  <LinkIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>LinkedIn</span>
                </a>
              )}
              {portfolio.contact_links.website && (
                <a
                  href={portfolio.contact_links.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
                  aria-label="Personal Website"
                >
                  <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Website</span>
                </a>
              )}
              {portfolio.contact_links.twitter && (
                <a
                  href={portfolio.contact_links.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
                  aria-label="Twitter Profile"
                >
                  <Share2 className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Twitter</span>
                </a>
              )}
            </div>
          )}
        </div>

        {/* Bio */}
        {portfolio.bio_override && (
          <div className="relative z-10 mt-6 pt-6 border-t border-border-subtle/50 text-sm text-text-secondary leading-relaxed max-w-4xl whitespace-pre-line">
            {portfolio.bio_override}
          </div>
        )}

        {/* Ambient glows */}
        <div
          aria-hidden="true"
          className="absolute -right-24 -bottom-24 h-64 w-64 rounded-full bg-accent-violet/10 blur-3xl pointer-events-none"
        />
        <div
          aria-hidden="true"
          className="absolute right-40 -top-20 h-48 w-48 rounded-full bg-accent-cyan/10 blur-2xl pointer-events-none"
        />
      </header>

      {/* Competencies & Skills Demonstrated Section */}
      {allSkills.length > 0 && (
        <section aria-labelledby="skills-heading" className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent-violet" aria-hidden="true" />
            <h2 id="skills-heading" className="text-sm font-semibold uppercase tracking-wider text-text-muted">
              Demonstrated Competencies ({allSkills.length})
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {allSkills.map((skill, idx) => (
              <span
                key={idx}
                className="inline-flex items-center rounded-lg bg-bg-elevated/70 px-3 py-1 text-xs font-mono text-text-primary border border-border-subtle hover:border-accent-violet/40 transition-colors"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Featured Projects & Deliverables Showcase */}
      <section aria-labelledby="projects-heading" className="space-y-6">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <FolderGit2 className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
            <h2 id="projects-heading" className="text-lg font-bold text-text-primary">
              Featured Capstones & Deliverables
            </h2>
          </div>
          <span className="text-xs text-text-muted font-mono">
            {portfolio.items.length} {portfolio.items.length === 1 ? 'project' : 'projects'}
          </span>
        </div>

        {portfolio.items.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {portfolio.items.map((item) => (
              <PortfolioItemCard key={item.id} item={item} isOwner={false} />
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-border-subtle bg-bg-elevated/30 p-12 text-center space-y-3">
            <FolderGit2 className="h-8 w-8 text-text-muted mx-auto" aria-hidden="true" />
            <h3 className="text-base font-semibold text-text-primary">No Featured Projects Yet</h3>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              This learner hasn't published any public capstone deliverables to their showcase yet.
            </p>
          </div>
        )}
      </section>

      {/* Footer Branding */}
      <footer className="pt-8 border-t border-border-subtle/50 text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 text-xs text-text-muted">
          <ShieldCheck className="h-3.5 w-3.5 text-accent-cyan" aria-hidden="true" />
          <span>Practical project deliverables independently verified on SkillVerse</span>
        </div>
        <div className="text-[11px] text-text-muted font-mono flex items-center justify-center gap-1">
          <Calendar className="h-3 w-3" aria-hidden="true" />
          <span>Showcase created: {new Date(portfolio.created_at).toLocaleDateString()}</span>
        </div>
      </footer>
    </div>
  )
}
