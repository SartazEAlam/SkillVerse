import React, { useState, useMemo } from 'react'
import {
  Sparkles,
  MessageSquare,
  Users,
  Target,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Info,
  Loader2,
} from 'lucide-react'
import type {
  CommunicationConfig,
  CommunicationSubmission,
} from '../../types/activity'
import type { CommunicationFeedbackResponse } from '../../types/ai'
import { aiApi } from '../../services/aiApi'

interface CommunicationActivityProps {
  activityId?: string
  config: CommunicationConfig
  submission: Partial<CommunicationSubmission>
  onChange: (updated: Partial<CommunicationSubmission>) => void
  disabled?: boolean
}

const DEFAULT_BLUF_SECTIONS = [
  {
    id: 'bottom_line',
    title: 'Bottom Line Up Front (BLUF)',
    prompt: 'State your recommendation, conclusion, or decision in 1-2 direct sentences.',
    min_words: 5,
  },
  {
    id: 'context_details',
    title: 'Context & Supporting Facts',
    prompt: 'Provide relevant context, background rationale, and critical evidence.',
    min_words: 10,
  },
  {
    id: 'next_steps',
    title: 'Next Steps & Clear Call to Action',
    prompt: 'Specify exact actions, deadlines, and decision points required.',
    min_words: 5,
  },
]

const DEFAULT_STAR_SECTIONS = [
  {
    id: 'situation',
    title: 'Situation',
    prompt: 'Describe the specific workplace context, challenge, or operational state.',
    min_words: 10,
  },
  {
    id: 'task',
    title: 'Task',
    prompt: 'What was your responsibility or objective in addressing this situation?',
    min_words: 10,
  },
  {
    id: 'action',
    title: 'Action',
    prompt: 'What specific, high-leverage steps did you take to resolve the challenge?',
    min_words: 10,
  },
  {
    id: 'result',
    title: 'Result',
    prompt: 'What was the quantifiable outcome, business impact, or lesson learned?',
    min_words: 10,
  },
]

export const CommunicationActivity: React.FC<CommunicationActivityProps> = ({
  activityId,
  config,
  submission,
  onChange,
  disabled = false,
}) => {
  const format = config.format || 'bluf'
  const sections = submission.sections || {}
  const reflection = submission.reflection || ''

  // AI Review state
  const [isReviewing, setIsReviewing] = useState<boolean>(false)
  const [aiFeedback, setAiFeedback] = useState<CommunicationFeedbackResponse | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)
  const [showGuidance, setShowGuidance] = useState<boolean>(true)

  const activeSections = useMemo(() => {
    if (config.sections && config.sections.length > 0) {
      return config.sections
    }
    return format === 'bluf' ? DEFAULT_BLUF_SECTIONS : DEFAULT_STAR_SECTIONS
  }, [config.sections, format])

  const handleSectionChange = (sectionId: string, value: string) => {
    if (disabled) return
    const updated = { ...sections, [sectionId]: value }
    onChange({
      format,
      sections: updated,
      reflection,
    })
  }

  const handleReflectionChange = (value: string) => {
    if (disabled) return
    onChange({
      format,
      sections,
      reflection: value,
    })
  }

  const requestAiFeedback = async () => {
    if (!activityId || isReviewing) return
    setIsReviewing(true)
    setAiError(null)

    try {
      const res = await aiApi.getCommunicationFeedback({
        activity_id: activityId,
        sections,
        reflection,
      })
      setAiFeedback(res)
    } catch (err: any) {
      if (err?.code === 'AI_FEATURE_OPTED_OUT' || err?.status === 403) {
        setAiError('AI Writing Review is disabled in your profile preferences.')
      } else if (err?.code === 'RATE_LIMIT_EXCEEDED' || err?.status === 429) {
        setAiError('Hourly AI feedback limit reached. Please try again later.')
      } else {
        setAiError(err?.message || 'Failed to generate AI writing review. Please try again.')
      }
    } finally {
      setIsReviewing(false)
    }
  }

  return (
    <div className="space-y-6 my-4 font-sans text-text-primary">
      {/* 1. Scenario Header & Context */}
      <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-accent-violet">
            <MessageSquare className="w-4 h-4" />
            <span>Communication Scenario</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-accent-violet/10 text-accent-violet border border-accent-violet/20 font-semibold">
              Format: {format.toUpperCase()}
            </span>
          </div>
        </div>

        <p className="text-sm text-text-primary leading-relaxed whitespace-pre-line font-medium">
          {config.scenario}
        </p>

        {(config.audience || config.objective) && (
          <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-border-subtle text-xs text-text-secondary">
            {config.audience && (
              <div className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-text-muted">Target Audience:</span>
                <span className="font-semibold text-text-primary">{config.audience}</span>
              </div>
            )}
            {config.objective && (
              <div className="flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-text-muted">Key Objective:</span>
                <span className="font-semibold text-text-primary">{config.objective}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. Format Guidance Toggle Banner */}
      <div className="p-3.5 rounded-xl bg-bg-surface border border-border-subtle">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
            <Info className="w-4 h-4 text-accent-cyan" />
            <span>
              {format === 'bluf'
                ? 'BLUF Best Practice: Bottom Line Up Front'
                : 'STAR Framework: Structured Narrative'}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowGuidance((prev) => !prev)}
            className="text-xs text-text-muted hover:text-text-primary underline cursor-pointer"
          >
            {showGuidance ? 'Hide Guidance' : 'Show Guidance'}
          </button>
        </div>

        {showGuidance && (
          <div className="mt-2.5 text-xs text-text-muted leading-relaxed space-y-1">
            {format === 'bluf' ? (
              <p>
                Lead with your primary recommendation or critical finding in the very first sentence.
                Busy executives need to make rapid decisions before delving into technical nuance.
              </p>
            ) : (
              <p>
                Structure your communication into Situation (context), Task (goal), Action (what you did),
                and Result (measurable outcome or lesson learned).
              </p>
            )}
          </div>
        )}
      </div>

      {/* 3. Structured Writing Section Inputs */}
      <div className="space-y-4">
        {activeSections.map((sec) => {
          const content = sections[sec.id] || ''
          const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0
          const minWords = sec.min_words || (format === 'bluf' && sec.id === 'bottom_line' ? 5 : 10)
          const isUnderMin = wordCount < minWords

          return (
            <div
              key={sec.id}
              className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-2 hover:border-border-medium transition-all"
            >
              <div className="flex items-center justify-between">
                <label
                  htmlFor={`sec-${sec.id}`}
                  className="text-xs font-semibold text-text-primary flex items-center gap-2"
                >
                  <span>{sec.title}</span>
                  <span className="text-accent-violet font-mono text-[10px]">*Required</span>
                </label>
                <span
                  className={`text-xs font-mono ${
                    content.trim() && isUnderMin ? 'text-accent-amber font-semibold' : 'text-text-muted'
                  }`}
                >
                  {wordCount} words {minWords > 0 && `(min ${minWords})`}
                </span>
              </div>

              <p className="text-xs text-text-muted leading-relaxed">{sec.prompt}</p>

              <textarea
                id={`sec-${sec.id}`}
                rows={format === 'bluf' && sec.id === 'bottom_line' ? 2 : 3}
                disabled={disabled}
                value={content}
                onChange={(e) => handleSectionChange(sec.id, e.target.value)}
                placeholder={`Draft your ${sec.title.toLowerCase()} here...`}
                className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet transition-all"
              />
            </div>
          )
        })}

        {/* Reflection */}
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="comm-reflection" className="text-xs font-semibold text-text-primary block">
              Communication Strategy Reflection (Optional)
            </label>
            <span className="text-xs font-mono text-text-muted">
              {reflection.trim() ? reflection.trim().split(/\s+/).length : 0} words
            </span>
          </div>
          <p className="text-xs text-text-muted">
            Why did you frame the message this way? How does it serve the target audience's needs?
          </p>
          <textarea
            id="comm-reflection"
            rows={2}
            disabled={disabled}
            value={reflection}
            onChange={(e) => handleReflectionChange(e.target.value)}
            placeholder="Brief reflection on your communication framing choices..."
            className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-border-medium text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet transition-all"
          />
        </div>
      </div>

      {/* 4. Optional AI Writing Review Card */}
      {activityId && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <button
              type="button"
              disabled={disabled || isReviewing}
              onClick={requestAiFeedback}
              className="px-4 py-2 rounded-xl bg-accent-violet/10 border border-accent-violet/30 hover:bg-accent-violet/20 text-accent-violet text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isReviewing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing Communication Structure...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Request AI Writing Review</span>
                </>
              )}
            </button>
            <span className="text-[11px] text-text-muted font-mono">
              Formative review — grades are evaluated on submission
            </span>
          </div>

          {aiError && (
            <div className="p-3 rounded-xl bg-state-error/10 border border-state-error/20 text-state-error text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{aiError}</span>
            </div>
          )}

          {aiFeedback && (
            <div className="p-4 rounded-xl bg-bg-surface border border-accent-violet/30 space-y-3.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-accent-violet">
                  <Sparkles className="w-4 h-4" />
                  <span>AI Writing Review ({aiFeedback.provider})</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-elevated border border-border-subtle text-text-muted">
                  Pedagogical Review
                </span>
              </div>

              <p className="text-xs text-text-primary leading-relaxed font-medium">
                {aiFeedback.summary}
              </p>

              {aiFeedback.strengths && aiFeedback.strengths.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-mono uppercase text-accent-emerald font-semibold block">
                    Key Strengths
                  </span>
                  <ul className="space-y-1 text-xs text-text-secondary">
                    {aiFeedback.strengths.map((s, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-accent-emerald shrink-0 mt-0.5" />
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {aiFeedback.improvements && aiFeedback.improvements.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-mono uppercase text-accent-amber font-semibold block">
                    Areas for Clarification
                  </span>
                  <ul className="space-y-1 text-xs text-text-secondary">
                    {aiFeedback.improvements.map((imp, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-accent-amber shrink-0 mt-0.5" />
                        <span>{imp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {aiFeedback.actionable_tips && aiFeedback.actionable_tips.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-mono uppercase text-accent-cyan font-semibold block">
                    Actionable Tips
                  </span>
                  <ul className="space-y-1 text-xs text-text-secondary">
                    {aiFeedback.actionable_tips.map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Lightbulb className="w-3.5 h-3.5 text-accent-cyan shrink-0 mt-0.5" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
