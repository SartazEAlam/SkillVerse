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
} from 'lucide-react'
import type { ApiLessonDetail } from '../../types/catalog'
import type { FlattenedLesson } from '../../types/lesson'
import type { ActivitySummary } from '../../types/activity'
import { fetchLessonActivities } from '../../services/activityApi'
import { ActivityContainer } from '../activities/ActivityContainer'
import { LessonRenderer } from './LessonRenderer'
import { Button } from '../../components/ui/Button'

interface LessonContentProps {
  lesson: ApiLessonDetail
  courseSlug: string
  moduleTitle?: string
  prevLesson: FlattenedLesson | null
  nextLesson: FlattenedLesson | null
}

export const LessonContent: React.FC<LessonContentProps> = ({
  lesson,
  courseSlug,
  moduleTitle,
  prevLesson,
  nextLesson,
}) => {
  const [activities, setActivities] = useState<ActivitySummary[]>([])

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
      .map((b) => (b.content as any)?.activity_id)
      .filter(Boolean)
  )

  const standaloneActivities = activities.filter((a) => !embeddedActivityIds.has(a.id))
  const learningObjectives = lesson.learning_objectives || []

  return (
    <article className="max-w-4xl mx-auto px-4 sm:px-8 py-8 sm:py-10 space-y-8 animate-fadeIn">
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
        </div>

        {/* Learning Objectives Box */}
        {learningObjectives.length > 0 && (
          <div
            role="region"
            aria-label="Lesson learning objectives"
            className="p-4 sm:p-5 rounded-xl bg-bg-elevated/70 border border-border-medium space-y-2.5 mt-4"
          >
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-text-primary">
              <Target className="w-4 h-4 text-accent-cyan" />
              <span>Learning Objectives</span>
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-text-secondary">
              {learningObjectives.map((obj, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-state-success shrink-0 mt-0.5" />
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </header>

      {/* Main Structured Educational Content Blocks */}
      <section aria-label="Lesson content">
        <LessonRenderer blocks={lesson.blocks || []} />
      </section>

      {/* Interactive Assessment Activities (if not already embedded in blocks) */}
      {standaloneActivities.length > 0 && (
        <section aria-label="Lesson interactive activities" className="space-y-6 pt-4 border-t border-border-subtle">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent-violet" />
            <h2 className="text-xl font-extrabold text-text-primary tracking-tight">
              Interactive Assessment Checkpoint
            </h2>
          </div>
          {standaloneActivities.map((act) => (
            <ActivityContainer key={act.id} activityId={act.id} />
          ))}
        </section>
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
