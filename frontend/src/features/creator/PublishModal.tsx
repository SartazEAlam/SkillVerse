import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  X,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react'
import type { CoursePublishResponse, DraftValidationResponse } from '../../types/creator'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface PublishModalProps {
  courseId: string
  courseSlug: string
  courseTitle: string
  isOpen: boolean
  onClose: () => void
  onPublished: (version: CoursePublishResponse) => void
}

export const PublishModal: React.FC<PublishModalProps> = ({
  courseId,
  courseSlug,
  courseTitle,
  isOpen,
  onClose,
  onPublished,
}) => {
  const [validating, setValidating] = useState<boolean>(true)
  const [validation, setValidation] = useState<DraftValidationResponse | null>(null)
  const [changelog, setChangelog] = useState<string>('')
  const [publishing, setPublishing] = useState<boolean>(false)
  const [publishedVersion, setPublishedVersion] = useState<CoursePublishResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) {
      setPublishedVersion(null)
      setError(null)
      return
    }

    const checkDraft = async () => {
      setValidating(true)
      setError(null)
      try {
        const val = await creatorApi.validateDraft(courseId)
        setValidation(val)
      } catch (err: unknown) {
        const e = err as { message?: string }
        setError(e.message || 'Failed to validate course draft.')
      } finally {
        setValidating(false)
      }
    }

    checkDraft()
  }, [isOpen, courseId])

  if (!isOpen) return null

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault()
    setPublishing(true)
    setError(null)

    try {
      const res = await creatorApi.publishCourse(courseId, changelog.trim() || undefined)
      setPublishedVersion(res)
      onPublished(res)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to publish course.')
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950/60 rounded-xl text-indigo-400 border border-indigo-800/40">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Publish Course Version</h2>
              <p className="text-xs text-slate-400 truncate max-w-xs">{courseTitle}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-2 text-red-200 text-xs">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {validating ? (
            <div className="p-8 text-center space-y-2">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-sm font-medium text-slate-300">Checking course publication requirements...</p>
            </div>
          ) : publishedVersion ? (
            <div className="p-6 bg-emerald-950/30 border border-emerald-800/60 rounded-xl space-y-4 text-center">
              <div className="p-3 bg-emerald-900/50 text-emerald-400 w-12 h-12 rounded-2xl mx-auto flex items-center justify-center border border-emerald-700/50">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-emerald-200">
                  Version {publishedVersion.version_number} Published Successfully!
                </h3>
                <p className="text-xs text-emerald-300/80 mt-1">
                  Your course is now active in the public catalog and ready for learner enrollments.
                </p>
              </div>

              <div className="pt-2 flex justify-center gap-3">
                <Link
                  to={`/courses/${courseSlug}`}
                  target="_blank"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  View in Catalog
                </Link>
                <Button type="button" variant="outline" size="sm" onClick={onClose}>
                  Done
                </Button>
              </div>
            </div>
          ) : !validation?.valid ? (
            <div className="space-y-4">
              <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-red-200 font-bold text-sm">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  Cannot Publish: Validation Errors Detected
                </div>
                <p className="text-xs text-red-300/80">
                  Please fix the following issues in the curriculum or metadata before publishing:
                </p>
                <ul className="list-disc list-inside text-xs text-red-300/90 space-y-1 pt-1">
                  {validation?.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx} className="truncate">
                      {err.title ? `${err.title}: ` : ''}
                      {err.message}
                    </li>
                  ))}
                  {(validation?.errors.length || 0) > 5 && (
                    <li className="italic">
                      +{validation!.errors.length - 5} more issues...
                    </li>
                  )}
                </ul>
              </div>

              <Button type="button" variant="ghost" onClick={onClose} className="w-full text-xs">
                Close &amp; Fix Issues
              </Button>
            </div>
          ) : (
            <form onSubmit={handlePublish} className="space-y-4">
              <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                <div className="text-xs text-slate-300 leading-relaxed">
                  <span className="font-semibold text-slate-100 block mb-0.5">
                    Immutable Version Guarantee
                  </span>
                  Publishing freezes this draft into an immutable snapshot. Future changes will create
                  a new working draft without disrupting existing learner progress.
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Version Changelog / Release Notes
                </label>
                <textarea
                  rows={3}
                  value={changelog}
                  onChange={(e) => setChangelog(e.target.value)}
                  placeholder="e.g. Initial public release, or Summary of updates and new exercises..."
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <Button type="button" variant="ghost" onClick={onClose} disabled={publishing}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={publishing}
                  className="flex items-center gap-2 text-xs"
                >
                  <UploadCloud className="w-4 h-4" />
                  {publishing ? 'Publishing...' : 'Confirm & Publish'}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
