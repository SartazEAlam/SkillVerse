import React from 'react'
import {
  FolderGit2,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  Edit2,
  Trash2,
  Download,
  Lock,
  Globe,
  Sparkles,
  Award,
  FileArchive,
  FileImage,
  FileCode,
  FileText,
} from 'lucide-react'
import type { PortfolioItem } from '../../types/portfolio'

interface PortfolioItemCardProps {
  item: PortfolioItem
  isOwner?: boolean
  isFirst?: boolean
  isLast?: boolean
  onMoveUp?: (itemId: string) => void
  onMoveDown?: (itemId: string) => void
  onEdit?: (item: PortfolioItem) => void
  onDelete?: (itemId: string) => void
}

export const PortfolioItemCard: React.FC<PortfolioItemCardProps> = ({
  item,
  isOwner = false,
  isFirst = false,
  isLast = false,
  onMoveUp,
  onMoveDown,
  onEdit,
  onDelete,
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileIcon = (filename: string) => {
    const lower = filename.toLowerCase()
    if (lower.endsWith('.zip') || lower.endsWith('.tar.gz') || lower.endsWith('.tgz')) {
      return <FileArchive className="h-3.5 w-3.5 text-accent-cyan" aria-hidden="true" />
    }
    if (
      lower.endsWith('.png') ||
      lower.endsWith('.jpg') ||
      lower.endsWith('.jpeg') ||
      lower.endsWith('.webp')
    ) {
      return <FileImage className="h-3.5 w-3.5 text-accent-violet" aria-hidden="true" />
    }
    if (lower.endsWith('.json') || lower.endsWith('.csv')) {
      return <FileCode className="h-3.5 w-3.5 text-state-warning" aria-hidden="true" />
    }
    return <FileText className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
  }

  const getItemTypeBadge = () => {
    switch (item.item_type) {
      case 'PROJECT_SUBMISSION':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-accent-violet/15 px-2 py-0.5 text-[11px] font-semibold text-accent-violet border border-accent-violet/30">
            <FolderGit2 className="h-3 w-3" aria-hidden="true" />
            <span>Capstone Project</span>
          </span>
        )
      case 'SKILL_MASTERY':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-accent-cyan/15 px-2 py-0.5 text-[11px] font-semibold text-accent-cyan border border-accent-cyan/30">
            <Sparkles className="h-3 w-3" aria-hidden="true" />
            <span>Skill Mastery</span>
          </span>
        )
      case 'ACHIEVEMENT':
        return (
          <span className="inline-flex items-center gap-1 rounded bg-state-warning/15 px-2 py-0.5 text-[11px] font-semibold text-state-warning border border-state-warning/30">
            <Award className="h-3 w-3" aria-hidden="true" />
            <span>Achievement</span>
          </span>
        )
      case 'CUSTOM':
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded bg-bg-surface px-2 py-0.5 text-[11px] font-medium text-text-secondary border border-border-subtle">
            <span>Showcase Item</span>
          </span>
        )
    }
  }

  return (
    <article
      className="group relative rounded-2xl border border-border-subtle bg-bg-elevated/40 p-5 sm:p-6 backdrop-blur-sm transition-all hover:border-border-medium hover:bg-bg-elevated/70 space-y-4"
      aria-label={`Portfolio item: ${item.title}`}
    >
      {/* Header Row */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {getItemTypeBadge()}
            {isOwner && (
              <span
                className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-mono border ${
                  item.visibility === 'PUBLIC'
                    ? 'border-state-success/30 bg-state-success/10 text-state-success'
                    : 'border-border-subtle bg-bg-surface text-text-muted'
                }`}
              >
                {item.visibility === 'PUBLIC' ? (
                  <>
                    <Globe className="h-2.5 w-2.5" aria-hidden="true" />
                    <span>Public</span>
                  </>
                ) : (
                  <>
                    <Lock className="h-2.5 w-2.5" aria-hidden="true" />
                    <span>Private</span>
                  </>
                )}
              </span>
            )}
          </div>

          <h3 className="text-base sm:text-lg font-bold tracking-tight text-text-primary">
            {item.title}
          </h3>
        </div>

        {/* Reorder and Owner Actions */}
        {isOwner && (
          <div className="flex items-center gap-1 shrink-0 bg-bg-surface/80 rounded-lg p-1 border border-border-subtle">
            <button
              type="button"
              onClick={() => onMoveUp && onMoveUp(item.id)}
              disabled={isFirst}
              className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-violet cursor-pointer"
              aria-label={`Move ${item.title} up`}
              title="Move item up in display order"
            >
              <ChevronUp className="h-4 w-4" aria-hidden="true" />
            </button>

            <button
              type="button"
              onClick={() => onMoveDown && onMoveDown(item.id)}
              disabled={isLast}
              className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-violet cursor-pointer"
              aria-label={`Move ${item.title} down`}
              title="Move item down in display order"
            >
              <ChevronDown className="h-4 w-4" aria-hidden="true" />
            </button>

            <div className="h-3.5 w-px bg-border-subtle mx-0.5" aria-hidden="true" />

            <button
              type="button"
              onClick={() => onEdit && onEdit(item)}
              className="p-1 rounded text-text-secondary hover:text-accent-cyan hover:bg-bg-elevated transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan cursor-pointer"
              aria-label={`Edit ${item.title}`}
              title="Edit portfolio item"
            >
              <Edit2 className="h-3.5 w-3.5" aria-hidden="true" />
            </button>

            <button
              type="button"
              onClick={() => onDelete && onDelete(item.id)}
              className="p-1 rounded text-state-error/70 hover:text-state-error hover:bg-state-error/10 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-state-error cursor-pointer"
              aria-label={`Delete ${item.title}`}
              title="Remove from portfolio"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      {/* Summary / Description */}
      {item.summary && (
        <p className="text-xs sm:text-sm text-text-secondary leading-relaxed whitespace-pre-line">
          {item.summary}
        </p>
      )}

      {/* Skills Demonstrated */}
      {item.skills_demonstrated && item.skills_demonstrated.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Skills Demonstrated
          </span>
          <div className="flex flex-wrap gap-1.5">
            {item.skills_demonstrated.map((skill, idx) => (
              <span
                key={idx}
                className="inline-flex items-center rounded-md bg-bg-surface px-2 py-0.5 text-xs text-text-secondary border border-border-subtle font-mono"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Public Artifacts */}
      {item.artifacts && item.artifacts.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border-subtle/50">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Verified Deliverables & Artifacts
          </span>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2" aria-label="Deliverable files">
            {item.artifacts.map((artifact) => (
              <li
                key={artifact.id}
                className="flex items-center justify-between gap-2 rounded-lg border border-border-subtle bg-bg-surface/60 px-2.5 py-1.5 text-xs"
              >
                <div className="flex items-center gap-2 min-w-0">
                  {getFileIcon(artifact.original_filename)}
                  <span className="font-mono text-text-primary truncate" title={artifact.original_filename}>
                    {artifact.original_filename}
                  </span>
                  <span className="text-[10px] text-text-muted shrink-0">
                    ({formatFileSize(artifact.file_size_bytes)})
                  </span>
                </div>

                <a
                  href={artifact.download_url}
                  download={artifact.original_filename}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1 rounded text-text-muted hover:text-accent-cyan transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan cursor-pointer shrink-0"
                  aria-label={`Download ${artifact.original_filename}`}
                  title="Download artifact"
                >
                  <Download className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* External Link */}
      {item.external_url && (
        <div className="pt-2 flex items-center justify-end">
          <a
            href={item.external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent-cyan hover:text-accent-cyan-hover underline underline-offset-4 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet rounded px-1"
          >
            <span>View Live Project</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
        </div>
      )}
    </article>
  )
}

