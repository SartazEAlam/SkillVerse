import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Clock,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Compass,
  Target,
  Sparkles,
  AlertCircle,
  PartyPopper,
} from 'lucide-react'
import type { ApiLessonDetail } from '../../types/catalog'
import type { FlattenedLesson } from '../../types/lesson'
import type { ActivitySummary } from '../../types/activity'
import { fetchLessonActivities } from '../../services/activityApi'
import { progressApi } from '../../services/progressApi'
import { ActivityContainer } from '../activities/ActivityContainer'
import { LessonRenderer } from './LessonRenderer'
import { Button } from '../../components/ui/Button'

interface LessonContentProps {
  lesson: ApiLessonDetail
  courseSlug: string
  moduleTitle?: string
  prevLesson: FlattenedLesson | null
  nextLesson: FlattenedLesson | null
  enrollmentId?: string
  onProgressUpdated?: (completedSlug?: string) => void
}

export const LessonContent: React.FC<LessonContentProps> = ({
  lesson,
  courseSlug,
  moduleTitle,
  prevLesson,
  nextLesson,
  enrollmentId,
  onProgressUpdated,
}) => {
  const [activities, setActivities] = useState<ActivitySummary[]>([])
  const [isCompleting, setIsCompleting] = useState<boolean>(false)
  const [completeError, setCompleteError] = useState<string | null>(null)
  const [courseCompletedBanner, setCourseCompletedBanner] = useState<boolean>(false)

  useEffect(() => {
    let isMounted = true
    if (lesson?.id) {
      fetchLessonActivities(lesson.id)
        .then((data) => {
          if (isMounted) setActivities(data)
        })
        .catch(() => {
          if (isMounted) setActivities([])
        })
    }
    return () => {
      isMounted = false
    }
  }, [lesson?.id])

  // Identify activities already rendered inside lesson.blocks
  const embeddedActivityIds = new Set(
    (lesson.blocks || [])
      .filter((b) => b.block_type === 'activity')
      .map((b) => (b.content as Record<string, unknown> | null)?.activity_id as string | undefined)
      .filter(Boolean)
  )

  const standaloneActivities = activities.filter((a) => !embeddedActivityIds.has(a.id))
  const learningObjectives = lesson.learning_objectives || []

  const handleCompleteLesson = async () => {
    if (!enrollmentId || !lesson.id) return
    setIsCompleting(true)
    setCompleteError(null)

    try {
      const resp = await progressApi.completeLesson(enrollmentId, lesson.id)
      if (resp.course_completed) {
        setCourseCompletedBanner(true)
      }
      if (onProgressUpdated) {
        onProgressUpdated(lesson.slug)
      }
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setCompleteError(apiErr.message || 'Complete all required activities before finishing this lesson.')
    } finally {
      setIsCompleting(false)
    }
  }

  return (
    <article className="max-w-4xl mx-auto px-4 sm:px-8 py-8 sm:py-10 space-y-8 animate-fadeIn">
      {/* Course Completion Celebration Banner */}
      {courseCompletedBanner && (
        <div className="p-4 rounded-xl bg-accent-violet/15 border border-accent-violet/40 flex items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-violet/20 flex items-center justify-center text-accent-violet">
              <PartyPopper className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">Course Completed! 🎉</h3>
              <p className="text-xs text-text-secondary">
                You have passed all required lessons and assessments for this course version.
              </p>
            </div>
          </div>
          <Link to="/dashboard">
            <Button variant="primary" size="sm">
              View Progress
            </Button>
          </Link>
        </div>
      )}

      {/* Lesson Header Area */}
      <header className="space-y-4 border-b border-border-subtle/80 pb-6">
        {moduleTitle && (
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-accent-violet">
            {moduleTitle}
          </span>
        )}

        <h1 className="text-2xl sm:text-4xl font-extrabold text-text-primary tracking-tight leading-tight">
          {lesson.title}
        </h1>

        {lesson.description && (
          <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
            {lesson.description}
          </p>
        )}

        {/* Metadata bar */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-text-muted pt-1">
          {lesson.estimated_minutes && (
            <span className="flex items-center gap-1.5 bg-bg-surface px-2.5 py-1 rounded-md border border-border-subtle">
              <Clock className="w-3.5 h-3.5 text-accent-cyan" />
              <span>{lesson.estimated_minutes} min read</span>
            </span>
          )}

          <span className="flex items-center gap-1.5 bg-bg-surface px-2.5 py-1 rounded-md border border-border-subtle">
            <span>{lesson.blocks?.length || 0} Content Blocks</span>
          </span>

          {activities.length > 0 && (
            <span className="flex items-center gap-1.5 bg-bg-surface px-2.5 py-1 rounded-md border border-border-subtle">
              <Target className="w-3.5 h-3.5 text-accent-violet" />
              <span>{activities.length} {activities.length === 1 ? 'Activity' : 'Activities'}</span>
            </span>
          )}
        </div>

        {/* Learning Objectives Box */}
        {learningObjectives.length > 0 && (
          <div className="p-4 rounded-xl bg-bg-surface/50 border border-border-subtle space-y-2 mt-4">
            <span className="text-xs font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-accent-cyan" />
              <span>Learning Objectives</span>
            </span>
            <ul className="space-y-1.5 pt-1">
              {learningObjectives.map((obj, i) => (
                <li key={i} className="text-xs text-text-secondary flex items-start gap-2">
                  <span className="text-accent-cyan font-mono mt-0.5">•</span>
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </header>

      {/* Structured Content Blocks (Markdown, Code, Callout, etc.) */}
      <section aria-label="Lesson Content" className="space-y-6">
        {lesson.blocks && lesson.blocks.length > 0 ? (
          <LessonRenderer blocks={lesson.blocks} />
        ) : (
          <div className="p-8 text-center border border-dashed border-border-medium rounded-xl text-text-muted text-sm">
            <p>This lesson does not have structured content blocks published yet.</p>
          </div>
        )}
      </section>

      {/* Standalone Interactive Activities */}
      {standaloneActivities.length > 0 && (
        <section aria-label="Interactive Assessments" className="pt-6 border-t border-border-subtle space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent-violet" />
              <h2 className="text-lg font-bold text-text-primary">
                Interactive Checkpoints
              </h2>
            </div>
            <span className="text-xs font-mono text-text-muted">
              {standaloneActivities.length} {standaloneActivities.length === 1 ? 'Task' : 'Tasks'}
            </span>
          </div>
          {standaloneActivities.map((act) => (
            <ActivityContainer key={act.id} activityId={act.id} />
          ))}
        </section>
      )}

      {/* Completion Action Callout for Enrolled Learners */}
      {enrollmentId && (
        <div className="p-5 rounded-xl bg-bg-surface border border-border-medium space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-text-primary">Lesson Progression Status</h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Complete all required activities above, then record lesson completion.
              </p>
            </div>
            <Button
              variant="outline"
              size="md"
              onClick={handleCompleteLesson}
              isLoading={isCompleting}
              leftIcon={<CheckCircle2 className="w-4 h-4 text-state-success" />}
            >
              Mark Lesson Complete
            </Button>
          </div>
          {completeError && (
            <div className="p-2.5 rounded-lg bg-state-error/10 border border-state-error/30 text-xs text-state-error flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{completeError}</span>
            </div>
          )}
        </div>
      )}

      {/* Bottom Navigation & Controls */}
      <footer className="pt-8 border-t border-border-subtle/80 space-y-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Previous Lesson Link */}
          {prevLesson ? (
            <Link
              to={`/learn/${courseSlug}/${prevLesson.slug}`}
              className="w-full sm:w-auto"
            >
              <Button
                variant="outline"
                size="md"
                leftIcon={<ChevronLeft className="w-4 h-4" />}
                className="w-full sm:w-auto justify-start"
              >
                <div className="text-left">
                  <span className="block text-[10px] uppercase font-mono text-text-muted">Previous</span>
                  <span className="block text-xs font-semibold truncate max-w-[180px] sm:max-w-[200px]">
                    {prevLesson.title}
                  </span>
                </div>
              </Button>
            </Link>
          ) : (
            <Link to={`/courses/${courseSlug}`} className="w-full sm:w-auto">
              <Button
                variant="ghost"
                size="md"
                leftIcon={<ArrowLeft className="w-4 h-4" />}
                className="w-full sm:w-auto justify-start text-text-muted hover:text-text-primary"
              >
                Course Overview
              </Button>
            </Link>
          )}

          {/* Next Lesson Link */}
          {nextLesson ? (
            <Link
              to={`/learn/${courseSlug}/${nextLesson.slug}`}
              className="w-full sm:w-auto"
            >
              <Button
                variant="primary"
                size="md"
                rightIcon={<ChevronRight className="w-4 h-4" />}
                className="w-full sm:w-auto justify-end"
              >
                <div className="text-right">
                  <span className="block text-[10px] uppercase font-mono text-white/80">Next Lesson</span>
                  <span className="block text-xs font-semibold truncate max-w-[180px] sm:max-w-[200px]">
                    {nextLesson.title}
                  </span>
                </div>
              </Button>
            </Link>
          ) : (
            <Link to={`/courses/${courseSlug}`} className="w-full sm:w-auto">
              <Button
                variant="primary"
                size="md"
                leftIcon={<Compass className="w-4 h-4" />}
                className="w-full sm:w-auto"
              >
                Finish Course & Review
              </Button>
            </Link>
          )}
        </div>

        {/* Keyboard shortcut guidance banner */}
        <div className="flex items-center justify-between text-[11px] text-text-muted pt-2">
          <span className="hidden sm:inline font-mono">
            Navigation tip: Press <kbd className="px-1.5 py-0.5 rounded bg-bg-surface border border-border-subtle font-mono text-text-primary">←</kbd> and <kbd className="px-1.5 py-0.5 rounded bg-bg-surface border border-border-subtle font-mono text-text-primary">→</kbd> keys to switch lessons
          </span>
          <Link
            to={`/courses/${courseSlug}`}
            className="text-accent-cyan hover:underline ml-auto"
          >
            Back to Course Syllabus
          </Link>
        </div>
      </footer>
    </article>
  )
}
