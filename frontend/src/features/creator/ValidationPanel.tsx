import React, { useState, useEffect } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Folder,
  FileText,
  Code,
  BookOpen,
} from 'lucide-react'
import type { DraftValidationResponse } from '../../types/creator'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface ValidationPanelProps {
  courseId: string
  onJumpToLesson?: (lessonId: string) => void
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ courseId }) => {
  const [validation, setValidation] = useState<DraftValidationResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const runValidation = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await creatorApi.validateDraft(courseId)
      setValidation(res)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to run server-side publication validation.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    runValidation()
  }, [courseId])

  const getScopeIcon = (scope: string) => {
    switch (scope) {
      case 'course':
        return <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
      case 'module':
        return <Folder className="w-3.5 h-3.5 text-blue-400" />
      case 'lesson':
        return <FileText className="w-3.5 h-3.5 text-cyan-400" />
      case 'activity':
        return <Code className="w-3.5 h-3.5 text-purple-400" />
      default:
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Pre-Publication Validation</h3>
          <p className="text-xs text-slate-400">
            Automated server-side checks verify course structure, lesson documents, and grading integrity.
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={runValidation}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Run Validation
        </Button>
      </div>

      {error && (
        <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && !validation ? (
        <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-xl">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-300 font-medium">Validating course curriculum...</p>
        </div>
      ) : validation?.valid ? (
        <div className="p-6 bg-emerald-950/30 border border-emerald-800/60 rounded-xl space-y-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-900/60 rounded-xl text-emerald-400 border border-emerald-700/50">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-emerald-200">
                Draft is Valid for Publication
              </h4>
              <p className="text-xs text-emerald-400/80">
                All curriculum modules, lessons, content blocks, and interactive activities meet SkillVerse standards.
              </p>
            </div>
          </div>

          {validation.warnings.length > 0 && (
            <div className="mt-4 pt-4 border-t border-emerald-800/40 space-y-2">
              <h5 className="text-xs font-semibold text-amber-300 uppercase tracking-wider">
                Non-blocking suggestions ({validation.warnings.length})
              </h5>
              {validation.warnings.map((w, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span>{w.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-4 bg-red-950/30 border border-red-800/60 rounded-xl flex items-center gap-3">
            <XCircle className="w-6 h-6 text-red-400 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-red-200">
                {validation?.errors.length || 0} Publication Issues Found
              </h4>
              <p className="text-xs text-red-300/80">
                You must resolve all critical errors below before this course can be published into the catalog.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            {validation?.errors.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-slate-900/70 border border-slate-800 hover:border-slate-700 rounded-xl flex items-start gap-3 transition-colors"
              >
                <div className="p-1.5 bg-slate-800 rounded-lg shrink-0 mt-0.5">
                  {getScopeIcon(item.scope)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {item.scope}
                    </span>
                    {item.title && (
                      <span className="text-xs font-semibold text-slate-200 truncate">
                        {item.title}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-red-300/90 leading-relaxed">{item.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
