import React, { useEffect, useState } from 'react'
import {
  Sparkles,
  RotateCcw,
  Send,
  AlertTriangle,
  Lock,
  Layers,
  Lightbulb,
} from 'lucide-react'
import type { ActivityDetail, AttemptResponse } from '../../types/activity'
import {
  fetchActivity,
  fetchActivityAttempts,
  submitActivityAttempt,
} from '../../services/activityApi'
import { aiApi } from '../../services/aiApi'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../../components/ui/Button'
import { ActivityRenderer } from './ActivityRenderer'
import { SubmissionFeedback } from './SubmissionFeedback'
import { AttemptHistory } from './AttemptHistory'

interface ActivityContainerProps {
  activityId: string
  initialActivity?: ActivityDetail
  titleOverride?: string | null
  instructionsOverride?: string | null
}

export const ActivityContainer: React.FC<ActivityContainerProps> = ({
  activityId,
  initialActivity,
  titleOverride,
  instructionsOverride,
}) => {
  const { user } = useAuth()
  const [activity, setActivity] = useState<ActivityDetail | null>(initialActivity || null)
  const [loading, setLoading] = useState<boolean>(!initialActivity)
  const [fetchError, setFetchError] = useState<string | null>(null)

  const [submissionState, setSubmissionState] = useState<Record<string, any>>({})
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [latestAttempt, setLatestAttempt] = useState<AttemptResponse | null>(null)
  const [attempts, setAttempts] = useState<AttemptResponse[]>([])

  // Phase 8: Progressive Hints
  const [hints, setHints] = useState<Array<{ level: number; text: string; provider: string }>>([])
  const [isRequestingHint, setIsRequestingHint] = useState<boolean>(false)
  const [hintError, setHintError] = useState<string | null>(null)

  // 1. Fetch activity definition
  useEffect(() => {
    let isMounted = true

    async function loadActivity() {
      if (initialActivity) {
        setActivity(initialActivity)
        return
      }

      setLoading(true)
      setFetchError(null)
      try {
        const data = await fetchActivity(activityId)
        if (isMounted) {
          setActivity(data)
        }
      } catch (err: any) {
        if (isMounted) {
          setFetchError(err.message || 'Failed to load interactive activity.')
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadActivity()
    return () => {
      isMounted = false
    }
  }, [activityId, initialActivity])

  // 2. Fetch past attempts if user is logged in
  useEffect(() => {
    let isMounted = true

    async function loadAttempts() {
      if (!user) {
        setAttempts([])
        setLatestAttempt(null)
        return
      }

      try {
        const data = await fetchActivityAttempts(activityId)
        if (isMounted && data.attempts.length > 0) {
          setAttempts(data.attempts)
          setLatestAttempt(data.attempts[0]) // latest attempt is index 0
        }
      } catch {
        // Silently fail attempt history fetch if unauthenticated
      }
    }

    loadAttempts()
    return () => {
      isMounted = false
    }
  }, [activityId, user])

  // 3. Local validation before submission
  const validateSubmission = (): string | null => {
    if (!activity) return 'Activity not loaded.'

    switch (activity.activity_type) {
      case 'single_choice':
        if (!submissionState.selected_option_id) {
          return 'Please select an option before submitting.'
        }
        break
      case 'multiple_select':
        if (
          !submissionState.selected_option_ids ||
          submissionState.selected_option_ids.length === 0
        ) {
          return 'Please select at least one option before submitting.'
        }
        break
      case 'true_false':
        if (typeof submissionState.selected_boolean !== 'boolean') {
          return 'Please choose True or False.'
        }
        break
      case 'short_answer':
        if (!submissionState.text || !submissionState.text.trim()) {
          return 'Please enter your response.'
        }
        break
      case 'fill_in_the_blank': {
        const blanks = activity.configuration.blanks || []
        const answers = submissionState.answers || {}
        const filled = blanks.filter((b: any) => answers[b.id]?.trim())
        if (filled.length === 0) {
          return 'Please fill in at least one blank.'
        }
        break
      }
      case 'matching': {
        const leftItems = activity.configuration.left_items || []
        const pairs = submissionState.pairs || {}
        if (Object.keys(pairs).length < leftItems.length) {
          return 'Please match all pairs before submitting.'
        }
        break
      }
      case 'scenario':
        if (!submissionState.selected_decision_id) {
          return 'Please select a decision option.'
        }
        break
      case 'code_exercise':
        if (
          typeof submissionState.code !== 'string' ||
          !submissionState.code.trim()
        ) {
          return 'Please enter your code before submitting.'
        }
        break
      default:
        break
    }
    return null
  }

  // 4. Submit attempt
  const handleSubmit = async () => {
    if (isSubmitting) return

    if (!user) {
      setSubmitError('Please sign in to submit your answer and record your progress.')
      return
    }

    const valErr = validateSubmission()
    if (valErr) {
      setSubmitError(valErr)
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const response = await submitActivityAttempt(activityId, submissionState)
      setLatestAttempt(response)
      setAttempts((prev) => [response, ...prev])
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to submit attempt. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // 5. Handle Retry
  const handleRetry = () => {
    setLatestAttempt(null)
    setSubmissionState({})
    setSubmitError(null)
  }

  // 6. Handle Progressive Hint Request
  const handleRequestHint = async () => {
    if (!activity || isRequestingHint) return
    const nextLevel = hints.length + 1
    if (nextLevel > 3) return

    setIsRequestingHint(true)
    setHintError(null)

    try {
      const res = await aiApi.getActivityHint({
        activity_id: activity.id,
        hint_level: nextLevel,
      })
      setHints((prev) => [
        ...prev,
        { level: res.hint_level, text: res.hint, provider: res.provider },
      ])
    } catch (err: any) {
      if (err?.code === 'AI_FEATURE_OPTED_OUT' || err?.status === 403) {
        setHintError('AI hints are disabled in your profile preferences.')
      } else if (err?.code === 'RATE_LIMIT_EXCEEDED' || err?.status === 429) {
        setHintError('Hourly hint limit reached (10/hr). Try breaking the problem down into smaller parts!')
      } else {
        setHintError(err?.message || 'Failed to retrieve progressive hint.')
      }
    } finally {
      setIsRequestingHint(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-subtle my-6 animate-pulse space-y-4">
        <div className="h-4 bg-bg-elevated rounded w-1/3" />
        <div className="h-6 bg-bg-elevated rounded w-2/3" />
        <div className="h-24 bg-bg-elevated rounded" />
      </div>
    )
  }

  if (fetchError || !activity) {
    return (
      <div className="p-5 rounded-2xl bg-bg-surface border border-state-error/30 text-state-error my-6 space-y-2 text-sm">
        <div className="flex items-center gap-2 font-bold">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Activity Unavailable</span>
        </div>
        <p className="text-text-muted">{fetchError || 'Activity definition not found.'}</p>
      </div>
    )
  }

  const title = titleOverride || activity.title
  const instructions = instructionsOverride || activity.instructions
  const isGraded = latestAttempt !== null
  const canRetry = latestAttempt?.can_retry ?? true

  return (
    <div
      role="region"
      aria-label={`Interactive Activity: ${title}`}
      className="p-5 sm:p-7 rounded-2xl bg-bg-elevated border border-border-medium shadow-md my-8 space-y-5 transition-all"
    >
      {/* Activity Header */}
      <div className="space-y-2 border-b border-border-subtle pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent-violet/15 text-accent-violet border border-accent-violet/25 text-[11px] font-mono font-bold uppercase tracking-wider">
            <Sparkles className="w-3 h-3" />
            <span>Interactive Assessment</span>
          </span>

          <div className="flex items-center gap-3 text-xs font-mono text-text-muted">
            {activity.max_attempts && (
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-accent-cyan" />
                <span>Max Attempts: {activity.max_attempts}</span>
              </span>
            )}
            <span>Pass Threshold: {activity.passing_score}%</span>
          </div>
        </div>

        <h3 className="text-lg sm:text-xl font-bold text-text-primary tracking-tight">
          {title}
        </h3>

        {instructions && (
          <p className="text-sm text-text-secondary leading-relaxed">
            {instructions}
          </p>
        )}
      </div>

      {/* Interactive Form Component */}
      <ActivityRenderer
        activity={activity}
        submissionState={submissionState}
        onSubmissionChange={(newState) => {
          setSubmissionState(newState)
          setSubmitError(null)
        }}
        disabled={isGraded || isSubmitting}
      />

      {/* Submission Feedback Result Area */}
      {latestAttempt && (
        <SubmissionFeedback
          attempt={latestAttempt}
          passingScore={activity.passing_score}
        />
      )}

      {/* Progressive Hints Area */}
      {hints.length > 0 && (
        <div className="space-y-2.5 pt-3 border-t border-border-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-accent-cyan" />
              <span>Progressive Hint Guidance ({hints.length}/3)</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan uppercase">
              {hints[hints.length - 1].provider}
            </span>
          </div>

          <div className="space-y-2">
            {hints.map((h) => (
              <div
                key={h.level}
                className="p-3.5 rounded-xl bg-accent-cyan/5 border border-accent-cyan/25 text-xs text-text-secondary leading-relaxed space-y-1"
              >
                <div className="font-semibold text-accent-cyan flex items-center gap-1.5">
                  <span>Level {h.level}</span>
                  <span className="text-text-muted">•</span>
                  <span>
                    {h.level === 1
                      ? 'Directional Nudge'
                      : h.level === 2
                      ? 'Core Principle'
                      : 'Structural Guidance'}
                  </span>
                </div>
                <div className="text-text-primary whitespace-pre-wrap">{h.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hint Error Alert */}
      {hintError && (
        <div
          role="alert"
          className="p-3 rounded-xl bg-state-warning/10 border border-state-warning/30 text-state-warning text-xs flex items-center gap-2"
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{hintError}</span>
        </div>
      )}

      {/* Local / Server Validation Error Notification */}
      {submitError && (
        <div
          role="alert"
          className="p-3.5 rounded-xl bg-state-error/10 border border-state-error/30 text-state-error text-xs sm:text-sm font-medium flex items-center gap-2"
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{submitError}</span>
        </div>
      )}

      {/* Action Bar (Submit / Retry / Login Prompt) */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-border-subtle">
        <div>
          {attempts.length > 0 && <AttemptHistory attempts={attempts} />}
        </div>

        <div className="flex items-center gap-3">
          {/* Progressive Hint Trigger Button */}
          {user && !isGraded && hints.length < 3 && (
            <Button
              type="button"
              variant="outline"
              size="md"
              isLoading={isRequestingHint}
              leftIcon={<Lightbulb className="w-4 h-4 text-accent-cyan" />}
              onClick={handleRequestHint}
              aria-label="Request progressive hint"
            >
              {hints.length === 0 ? 'Need a Hint?' : `Hint (${hints.length + 1}/3)`}
            </Button>
          )}

          {!user ? (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <Lock className="w-3.5 h-3.5 text-accent-violet" />
              <span>Log in to submit and record score</span>
            </div>
          ) : isGraded ? (
            canRetry ? (
              <Button
                variant="outline"
                size="md"
                leftIcon={<RotateCcw className="w-4 h-4" />}
                onClick={handleRetry}
              >
                Retry Activity
              </Button>
            ) : (
              <span className="text-xs font-mono text-text-muted py-2">
                Attempt limit reached ({activity.max_attempts} of {activity.max_attempts})
              </span>
            )
          ) : (
            <Button
              variant="primary"
              size="md"
              isLoading={isSubmitting}
              leftIcon={<Send className="w-4 h-4" />}
              onClick={handleSubmit}
            >
              Submit Answer
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
