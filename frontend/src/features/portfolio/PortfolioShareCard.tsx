import React, { useState } from 'react'
import { Link } from 'lucide-react'
import {
  Share2,
  Copy,
  Check,
  ExternalLink,
  Lock,
  Globe,
  EyeOff,
  AlertCircle,
} from 'lucide-react'
import type { PortfolioVisibility } from '../../types/portfolio'

interface PortfolioShareCardProps {
  visibility: PortfolioVisibility | string
  customSlug: string | null
  userId: string
}

export const PortfolioShareCard: React.FC<PortfolioShareCardProps> = ({
  visibility,
  customSlug,
  userId,
}) => {
  const [copied, setCopied] = useState(false)

  const identifier = customSlug || userId
  const sharePath = `/u/${encodeURIComponent(identifier)}/portfolio`
  const shareUrl = `${window.location.origin}${sharePath}`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      // Fallback
    }
  }

  const getVisibilityBadge = () => {
    switch (visibility) {
      case 'PUBLIC':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-state-success/10 px-3 py-1 text-xs font-semibold text-state-success border border-state-success/20">
            <Globe className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Public Showcase</span>
          </span>
        )
      case 'UNLISTED':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-state-warning/10 px-3 py-1 text-xs font-semibold text-state-warning border border-state-warning/20">
            <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Unlisted (Link Only)</span>
          </span>
        )
      case 'PRIVATE':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-bg-surface px-3 py-1 text-xs font-semibold text-text-muted border border-border-subtle">
            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Private Draft</span>
          </span>
        )
    }
  }

  return (
    <div className="rounded-2xl border border-border-subtle bg-bg-elevated/50 p-6 backdrop-blur-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Share2 className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-text-primary">Portfolio Share & Exposure</h2>
        </div>
        {getVisibilityBadge()}
      </div>

      <p className="text-xs text-text-secondary leading-relaxed">
        {visibility === 'PUBLIC' &&
          'Your portfolio is publicly accessible and discoverable. Anyone with this link can view your showcased public projects.'}
        {visibility === 'UNLISTED' &&
          'Your portfolio is unlisted. Only individuals with the exact direct link can view it; it will not appear in search or public discovery.'}
        {visibility === 'PRIVATE' &&
          'Your portfolio is currently private. Visitors will receive an access-denied message until you switch to Unlisted or Public.'}
      </p>

      {/* Share Link Row */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        <div className="flex-1 flex items-center rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-xs font-mono text-text-secondary overflow-hidden">
          <Link className="h-3.5 w-3.5 shrink-0 text-text-muted mr-2" aria-hidden="true" />
          <span className="truncate select-all">{shareUrl}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleCopy}
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 rounded-lg border border-border-subtle bg-bg-surface px-3.5 py-2 text-xs font-medium text-text-primary hover:bg-bg-elevated transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
            aria-label="Copy shareable portfolio link"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-state-success" aria-hidden="true" />
                <span className="text-state-success font-semibold">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
                <span>Copy Link</span>
              </>
            )}
          </button>

          <a
            href={sharePath}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 rounded-lg bg-accent-violet/10 border border-accent-violet/30 px-3.5 py-2 text-xs font-medium text-accent-violet hover:bg-accent-violet/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
            aria-label="Open public portfolio showcase in new tab"
          >
            <span>Preview</span>
            <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>
      </div>

      {visibility === 'PRIVATE' && (
        <div
          role="note"
          className="flex items-start gap-2 rounded-lg bg-state-warning/10 border border-state-warning/20 p-2.5 text-xs text-state-warning"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            Remember to set your visibility to <strong>Unlisted</strong> or <strong>Public</strong> when you are ready to share your portfolio with employers or peers.
          </span>
        </div>
      )}
    </div>
  )
}

