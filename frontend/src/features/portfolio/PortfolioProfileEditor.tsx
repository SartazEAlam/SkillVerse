import React, { useState } from 'react'
import {
  User,
  Globe,
  Lock,
  EyeOff,
  Code2,
  Share2,
  Link as LinkIcon,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import type {
  PortfolioDetail,
  PortfolioUpdateRequest,
  PortfolioVisibility,
} from '../../types/portfolio'
import { portfolioApi } from '../../services/portfolioApi'
import { ApiError } from '../../services/api'

interface PortfolioProfileEditorProps {
  portfolio: PortfolioDetail
  onPortfolioChange: (updated: PortfolioDetail) => void
}

export const PortfolioProfileEditor: React.FC<PortfolioProfileEditorProps> = ({
  portfolio,
  onPortfolioChange,
}) => {
  const [title, setTitle] = useState(portfolio.title || '')
  const [headline, setHeadline] = useState(portfolio.headline || '')
  const [bio, setBio] = useState(portfolio.bio_override || '')
  const [customSlug, setCustomSlug] = useState(portfolio.custom_slug || '')
  const [visibility, setVisibility] = useState<PortfolioVisibility>(
    (portfolio.visibility as PortfolioVisibility) || 'PRIVATE'
  )

  const [github, setGithub] = useState(portfolio.contact_links?.github || '')
  const [linkedin, setLinkedin] = useState(portfolio.contact_links?.linkedin || '')
  const [website, setWebsite] = useState(portfolio.contact_links?.website || '')
  const [twitter, setTwitter] = useState(portfolio.contact_links?.twitter || '')

  const [isSaving, setIsSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    // Validate custom slug client-side format
    const cleanedSlug = customSlug.trim().toLowerCase()
    if (cleanedSlug && !/^[a-zA-Z0-9_-]+$/.test(cleanedSlug)) {
      setErrorMsg('Custom slug must consist only of letters, numbers, hyphens, and underscores.')
      setIsSaving(false)
      return
    }

    try {
      const payload: PortfolioUpdateRequest = {
        title: title.trim() || undefined,
        headline: headline.trim() || undefined,
        bio_override: bio.trim() || undefined,
        custom_slug: cleanedSlug || undefined,
        visibility,
        contact_links: {
          github: github.trim() || undefined,
          linkedin: linkedin.trim() || undefined,
          website: website.trim() || undefined,
          twitter: twitter.trim() || undefined,
        },
      }

      const updated = await portfolioApi.updateMyPortfolio(payload)
      onPortfolioChange(updated)
      setSuccessMsg('Portfolio profile updated successfully.')
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message || 'Failed to update portfolio profile.')
      } else {
        setErrorMsg('Failed to save portfolio changes. Please check your connection.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-border-subtle bg-bg-elevated/40 p-6 backdrop-blur-sm space-y-6"
      aria-label="Portfolio Profile Settings"
    >
      <div className="flex items-center justify-between border-b border-border-subtle/60 pb-4">
        <div>
          <h2 className="text-base font-semibold text-text-primary flex items-center gap-2">
            <User className="h-4 w-4 text-accent-violet" aria-hidden="true" />
            <span>Profile & Publication Settings</span>
          </h2>
          <p className="text-xs text-text-muted mt-0.5">
            Customize how your public showcase appears to employers, peers, and collaborators.
          </p>
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-4 py-2 text-xs font-semibold text-white hover:bg-accent-violet-hover disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Save className="h-4 w-4" aria-hidden="true" />
          )}
          <span>{isSaving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-lg bg-state-success/10 border border-state-success/20 p-3 text-xs text-state-success"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Error Notification */}
      {errorMsg && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg bg-state-error/10 border border-state-error/20 p-3 text-xs text-state-error"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Title */}
        <div className="space-y-1.5">
          <label htmlFor="portfolio-title" className="block text-xs font-medium text-text-secondary">
            Showcase Title
          </label>
          <input
            id="portfolio-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Alex Chen's Engineering Portfolio"
            maxLength={200}
            className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet"
          />
        </div>

        {/* Custom Slug */}
        <div className="space-y-1.5">
          <label htmlFor="portfolio-slug" className="block text-xs font-medium text-text-secondary">
            Custom URL Handle (Slug)
          </label>
          <div className="flex rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet focus-within:ring-1 focus-within:ring-accent-violet">
            <span className="inline-flex items-center px-3 text-xs font-mono text-text-muted bg-bg-surface/50 border-r border-border-medium select-none">
              /u/
            </span>
            <input
              id="portfolio-slug"
              type="text"
              value={customSlug}
              onChange={(e) => setCustomSlug(e.target.value.toLowerCase())}
              placeholder="alex-chen"
              maxLength={100}
              className="flex-1 bg-transparent px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none"
            />
          </div>
          <p className="text-[11px] text-text-muted">
            Direct showcase link: <code>/u/{customSlug || '<handle>'}/portfolio</code>
          </p>
        </div>
      </div>

      {/* Professional Headline */}
      <div className="space-y-1.5">
        <label htmlFor="portfolio-headline" className="block text-xs font-medium text-text-secondary">
          Professional Headline
        </label>
        <input
          id="portfolio-headline"
          type="text"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="e.g. Full-Stack Developer specializing in React, TypeScript & Scalable APIs"
          maxLength={300}
          className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet"
        />
      </div>

      {/* Biography */}
      <div className="space-y-1.5">
        <label htmlFor="portfolio-bio" className="block text-xs font-medium text-text-secondary">
          Biography & Background
        </label>
        <textarea
          id="portfolio-bio"
          rows={4}
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Share your technical interests, past practical experience, and what you are learning on SkillVerse..."
          maxLength={5000}
          className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet resize-y"
        />
      </div>

      {/* Visibility Selector */}
      <div className="space-y-2">
        <span className="block text-xs font-medium text-text-secondary">
          Portfolio Exposure & Privacy
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Private */}
          <label
            className={`flex flex-col p-3.5 rounded-xl border cursor-pointer transition-all ${
              visibility === 'PRIVATE'
                ? 'border-accent-violet bg-accent-violet/10 text-text-primary shadow-sm'
                : 'border-border-subtle bg-bg-surface/50 text-text-secondary hover:border-border-medium'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 font-semibold text-xs">
                <Lock className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
                <span>PRIVATE</span>
              </div>
              <input
                type="radio"
                name="portfolio-visibility"
                value="PRIVATE"
                checked={visibility === 'PRIVATE'}
                onChange={() => setVisibility('PRIVATE')}
                className="text-accent-violet focus:ring-accent-violet"
              />
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Only accessible to you. Inaccessible to any visitor or employer.
            </p>
          </label>

          {/* Unlisted */}
          <label
            className={`flex flex-col p-3.5 rounded-xl border cursor-pointer transition-all ${
              visibility === 'UNLISTED'
                ? 'border-state-warning bg-state-warning/10 text-text-primary shadow-sm'
                : 'border-border-subtle bg-bg-surface/50 text-text-secondary hover:border-border-medium'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-state-warning">
                <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />
                <span>UNLISTED</span>
              </div>
              <input
                type="radio"
                name="portfolio-visibility"
                value="UNLISTED"
                checked={visibility === 'UNLISTED'}
                onChange={() => setVisibility('UNLISTED')}
                className="text-state-warning focus:ring-state-warning"
              />
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Accessible only via exact direct link. Excluded from public discovery.
            </p>
          </label>

          {/* Public */}
          <label
            className={`flex flex-col p-3.5 rounded-xl border cursor-pointer transition-all ${
              visibility === 'PUBLIC'
                ? 'border-state-success bg-state-success/10 text-text-primary shadow-sm'
                : 'border-border-subtle bg-bg-surface/50 text-text-secondary hover:border-border-medium'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-state-success">
                <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                <span>PUBLIC</span>
              </div>
              <input
                type="radio"
                name="portfolio-visibility"
                value="PUBLIC"
                checked={visibility === 'PUBLIC'}
                onChange={() => setVisibility('PUBLIC')}
                className="text-state-success focus:ring-state-success"
              />
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Freely accessible and discoverable. Ideal for resumes and job applications.
            </p>
          </label>
        </div>
      </div>

      {/* Social and Contact Links */}
      <div className="space-y-3 pt-2 border-t border-border-subtle/60">
        <span className="block text-xs font-semibold text-text-secondary">
          Public Contact & Social Links
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* GitHub */}
          <div className="flex items-center rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet">
            <span className="inline-flex items-center px-3 text-text-muted bg-bg-surface/50 border-r border-border-medium select-none" title="GitHub">
              <Code2 className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <input
              type="url"
              value={github}
              onChange={(e) => setGithub(e.target.value)}
              placeholder="https://github.com/username"
              className="flex-1 bg-transparent px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
              aria-label="GitHub Profile URL"
            />
          </div>

          {/* LinkedIn */}
          <div className="flex items-center rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet">
            <span className="inline-flex items-center px-3 text-text-muted bg-bg-surface/50 border-r border-border-medium select-none" title="LinkedIn">
              <LinkIcon className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <input
              type="url"
              value={linkedin}
              onChange={(e) => setLinkedin(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className="flex-1 bg-transparent px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
              aria-label="LinkedIn Profile URL"
            />
          </div>

          {/* Personal Website */}
          <div className="flex items-center rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet">
            <span className="inline-flex items-center px-3 text-text-muted bg-bg-surface/50 border-r border-border-medium select-none" title="Website">
              <Globe className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <input
              type="url"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://yourwebsite.dev"
              className="flex-1 bg-transparent px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
              aria-label="Personal Website URL"
            />
          </div>

          {/* Twitter / X */}
          <div className="flex items-center rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet">
            <span className="inline-flex items-center px-3 text-text-muted bg-bg-surface/50 border-r border-border-medium select-none" title="Social">
              <Share2 className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <input
              type="url"
              value={twitter}
              onChange={(e) => setTwitter(e.target.value)}
              placeholder="https://x.com/username"
              className="flex-1 bg-transparent px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
              aria-label="Twitter or X Profile URL"
            />
          </div>
        </div>
      </div>
    </form>
  )
}
