import React, { useState, useEffect } from 'react'
import {
  FolderGit2,
  Sparkles,
  Link as LinkIcon,
  Globe,
  Lock,
  Loader2,
  AlertCircle,
  Plus,
} from 'lucide-react'
import { Modal } from '../../components/ui/Modal'
import type {
  PortfolioItem,
  PortfolioItemCreateRequest,
  PortfolioItemType,
  PortfolioItemUpdateRequest,
  PortfolioVisibility,
} from '../../types/portfolio'
import type { SubmissionSummary } from '../../types/project'
import { portfolioApi } from '../../services/portfolioApi'
import { ApiError } from '../../services/api'

interface PortfolioItemModalProps {
  isOpen: boolean
  onClose: () => void
  itemToEdit?: PortfolioItem | null
  onItemSaved: () => void
}

export const PortfolioItemModal: React.FC<PortfolioItemModalProps> = ({
  isOpen,
  onClose,
  itemToEdit,
  onItemSaved,
}) => {
  const isEditing = Boolean(itemToEdit)

  const [itemType, setItemType] = useState<PortfolioItemType>('PROJECT_SUBMISSION')
  const [completedSubmissions, setCompletedSubmissions] = useState<SubmissionSummary[]>([])
  const [loadingSubmissions, setLoadingSubmissions] = useState(false)
  const [selectedSubmissionId, setSelectedSubmissionId] = useState('')

  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [skillsInput, setSkillsInput] = useState('')
  const [externalUrl, setExternalUrl] = useState('')
  const [visibility, setVisibility] = useState<PortfolioVisibility>('PUBLIC')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Reset or initialize fields
  useEffect(() => {
    if (!isOpen) return

    setErrorMessage(null)

    if (itemToEdit) {
      setTitle(itemToEdit.title || '')
      setSummary(itemToEdit.summary || '')
      setExternalUrl(itemToEdit.external_url || '')
      setVisibility((itemToEdit.visibility as PortfolioVisibility) || 'PUBLIC')
      setSkillsInput((itemToEdit.skills_demonstrated || []).join(', '))
      setItemType((itemToEdit.item_type as PortfolioItemType) || 'CUSTOM')
    } else {
      setTitle('')
      setSummary('')
      setExternalUrl('')
      setVisibility('PUBLIC')
      setSkillsInput('')
      setItemType('PROJECT_SUBMISSION')
      setSelectedSubmissionId('')

      // Fetch eligible completed submissions
      setLoadingSubmissions(true)
      portfolioApi
        .getCompletedSubmissions()
        .then((subs) => {
          setCompletedSubmissions(subs)
          if (subs.length > 0) {
            setSelectedSubmissionId(subs[0].id)
            setTitle(subs[0].title || 'Capstone Project Deliverable')
          } else {
            // Default to custom if no completed submissions exist
            setItemType('CUSTOM')
          }
        })
        .catch(() => {
          // If error loading submissions, default to custom
          setItemType('CUSTOM')
        })
        .finally(() => {
          setLoadingSubmissions(false)
        })
    }
  }, [isOpen, itemToEdit])

  const handleSubmissionChange = (subId: string) => {
    setSelectedSubmissionId(subId)
    const sub = completedSubmissions.find((s) => s.id === subId)
    if (sub) {
      setTitle(sub.title || 'Capstone Project Deliverable')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (isEditing && itemToEdit) {
      if (!title.trim()) {
        setErrorMessage('Item title cannot be empty.')
        return
      }

      try {
        setIsSubmitting(true)
        const updatePayload: PortfolioItemUpdateRequest = {
          title: title.trim(),
          summary: summary.trim() || undefined,
          external_url: externalUrl.trim() || undefined,
          visibility,
        }
        await portfolioApi.updatePortfolioItem(itemToEdit.id, updatePayload)
        onItemSaved()
        onClose()
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          setErrorMessage(err.message || 'Failed to update portfolio item.')
        } else {
          setErrorMessage('Failed to update portfolio item. Please try again.')
        }
      } finally {
        setIsSubmitting(false)
      }
    } else {
      // Adding new item
      if (itemType === 'PROJECT_SUBMISSION' && !selectedSubmissionId) {
        setErrorMessage('Please select a completed project submission to feature.')
        return
      }

      if (!title.trim()) {
        setErrorMessage('Please provide a title for this portfolio item.')
        return
      }

      const parsedSkills = skillsInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)

      try {
        setIsSubmitting(true)
        const createPayload: PortfolioItemCreateRequest = {
          item_type: itemType,
          reference_id: itemType === 'PROJECT_SUBMISSION' ? selectedSubmissionId : undefined,
          title: title.trim(),
          summary: summary.trim() || undefined,
          external_url: externalUrl.trim() || undefined,
          visibility,
          skills_demonstrated: parsedSkills,
        }

        await portfolioApi.addPortfolioItem(createPayload)
        onItemSaved()
        onClose()
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          setErrorMessage(err.message || 'Failed to add portfolio item.')
        } else {
          setErrorMessage('Failed to add portfolio item. Please try again.')
        }
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Portfolio Showcase Item' : 'Add Showcase Item'}
      description="Feature your practical skills, completed capstone deliverables, and professional achievements."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5" aria-label="Portfolio Item Form">
        {errorMessage && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-state-error/30 bg-state-error/10 p-3 text-xs text-state-error"
          >
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
            <span className="flex-1 leading-relaxed">{errorMessage}</span>
          </div>
        )}

        {/* Item Type Selection (only when creating) */}
        {!isEditing && (
          <div className="space-y-1.5">
            <span className="block text-xs font-semibold text-text-secondary">Item Type</span>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setItemType('PROJECT_SUBMISSION')}
                className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-xs font-semibold transition-all cursor-pointer ${
                  itemType === 'PROJECT_SUBMISSION'
                    ? 'border-accent-violet bg-accent-violet/10 text-text-primary ring-1 ring-accent-violet'
                    : 'border-border-subtle bg-bg-surface text-text-muted hover:border-border-medium'
                }`}
              >
                <FolderGit2 className="h-4 w-4 text-accent-violet" aria-hidden="true" />
                <span>Completed Capstone</span>
              </button>

              <button
                type="button"
                onClick={() => setItemType('CUSTOM')}
                className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-xs font-semibold transition-all cursor-pointer ${
                  itemType === 'CUSTOM'
                    ? 'border-accent-cyan bg-accent-cyan/10 text-text-primary ring-1 ring-accent-cyan'
                    : 'border-border-subtle bg-bg-surface text-text-muted hover:border-border-medium'
                }`}
              >
                <Sparkles className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
                <span>Custom Project / Work</span>
              </button>
            </div>
          </div>
        )}

        {/* Completed Submission Dropdown (if PROJECT_SUBMISSION) */}
        {!isEditing && itemType === 'PROJECT_SUBMISSION' && (
          <div className="space-y-1.5">
            <label
              htmlFor="submission-select"
              className="block text-xs font-medium text-text-secondary"
            >
              Select Completed Project Submission
            </label>
            {loadingSubmissions ? (
              <div className="flex items-center gap-2 text-xs text-text-muted py-2">
                <Loader2 className="h-4 w-4 animate-spin text-accent-violet" aria-hidden="true" />
                <span>Checking completed projects...</span>
              </div>
            ) : completedSubmissions.length > 0 ? (
              <select
                id="submission-select"
                value={selectedSubmissionId}
                onChange={(e) => handleSubmissionChange(e.target.value)}
                className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-xs text-text-primary focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet"
              >
                {completedSubmissions.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.title || 'Untitled Submission'} (Score: {sub.score ? `${sub.score}%` : 'Passed'}) &bull; Version {sub.version_number}
                  </option>
                ))}
              </select>
            ) : (
              <div className="rounded-lg border border-state-warning/30 bg-state-warning/10 p-3 text-xs text-state-warning">
                No completed project submissions found yet. Complete and pass a capstone project first, or create a custom showcase item below.
              </div>
            )}
            <p className="text-[11px] text-text-muted">
              Auto-imports demonstrated skills and public deliverable artifacts verified by evaluators.
            </p>
          </div>
        )}

        {/* Title */}
        <div className="space-y-1.5">
          <label htmlFor="item-title" className="block text-xs font-medium text-text-secondary">
            Item Title <span className="text-state-error">*</span>
          </label>
          <input
            id="item-title"
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Distributed Task Queue Service"
            maxLength={300}
            className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet"
          />
        </div>

        {/* Summary */}
        <div className="space-y-1.5">
          <label htmlFor="item-summary" className="block text-xs font-medium text-text-secondary">
            Summary & Impact Description
          </label>
          <textarea
            id="item-summary"
            rows={3}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Describe what you built, key technical challenges overcome, and practical outcomes..."
            maxLength={5000}
            className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet resize-y"
          />
        </div>

        {/* Custom Skills (for Custom items or override) */}
        {!isEditing && itemType === 'CUSTOM' && (
          <div className="space-y-1.5">
            <label htmlFor="item-skills" className="block text-xs font-medium text-text-secondary">
              Skills Demonstrated (comma-separated)
            </label>
            <input
              id="item-skills"
              type="text"
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder="e.g. TypeScript, React 19, FastAPI, PostgreSQL"
              className="w-full rounded-lg border border-border-medium bg-bg-base px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:border-accent-violet focus:outline-none focus:ring-1 focus:ring-accent-violet font-mono"
            />
          </div>
        )}

        {/* External URL */}
        <div className="space-y-1.5">
          <label htmlFor="item-external-url" className="block text-xs font-medium text-text-secondary">
            External Project or Demo Link (Optional)
          </label>
          <div className="flex items-center rounded-lg border border-border-medium bg-bg-base overflow-hidden focus-within:border-accent-violet">
            <span className="inline-flex items-center px-3 text-text-muted bg-bg-surface/50 border-r border-border-medium select-none">
              <LinkIcon className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
            <input
              id="item-external-url"
              type="url"
              value={externalUrl}
              onChange={(e) => setExternalUrl(e.target.value)}
              placeholder="https://github.com/yourname/project or https://project.dev"
              maxLength={500}
              className="flex-1 bg-transparent px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
            />
          </div>
        </div>

        {/* Item Visibility */}
        <div className="space-y-1.5">
          <span className="block text-xs font-semibold text-text-secondary">Item Visibility</span>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-xs text-text-primary cursor-pointer select-none">
              <input
                type="radio"
                name="item-visibility"
                value="PUBLIC"
                checked={visibility === 'PUBLIC'}
                onChange={() => setVisibility('PUBLIC')}
                className="text-accent-violet focus:ring-accent-violet"
              />
              <Globe className="h-3.5 w-3.5 text-state-success" aria-hidden="true" />
              <span>Public (Visible in public showcase)</span>
            </label>

            <label className="flex items-center gap-2 text-xs text-text-primary cursor-pointer select-none">
              <input
                type="radio"
                name="item-visibility"
                value="PRIVATE"
                checked={visibility === 'PRIVATE'}
                onChange={() => setVisibility('PRIVATE')}
                className="text-accent-violet focus:ring-accent-violet"
              />
              <Lock className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
              <span>Private (Only visible in your management workspace)</span>
            </label>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border-subtle">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg border border-border-subtle bg-bg-surface px-4 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-lg bg-accent-violet px-4 py-2 text-xs font-semibold text-white hover:bg-accent-violet-hover disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Plus className="h-4 w-4" aria-hidden="true" />
            )}
            <span>{isEditing ? 'Save Changes' : 'Add to Portfolio'}</span>
          </button>
        </div>
      </form>
    </Modal>
  )
}

