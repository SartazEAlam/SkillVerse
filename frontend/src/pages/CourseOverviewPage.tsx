import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Compass,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Play,
  Terminal,
  MessageSquare,
  FileQuestion,
  Sparkles,
  ArrowLeft,
  Info
} from 'lucide-react'
import { SAMPLE_COURSES } from '../data/courses'
import type { ActivityType } from '../types/course'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'

export const CourseOverviewPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>()
  const course = SAMPLE_COURSES.find((c) => c.slug === slug)

  // Track expanded modules (all expanded by default for discoverability)
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>({
    'mod-html-structure': true,
    'mod-css-layouts': true,
    'mod-js-basics': true,
    'mod-comm-1': true,
    'mod-comm-2': true,
    'mod-comm-3': true,
    'mod-prod-1': true,
    'mod-prod-2': true,
    'mod-prod-3': true,
    'mod-design-1': true,
    'mod-design-2': true,
    'mod-think-1': true,
    'mod-think-2': true
  })

  // Modal state for lesson preview
  const [previewModalOpen, setPreviewModalOpen] = useState(false)
  const [previewLessonTitle, setPreviewLessonTitle] = useState('')

  if (!course) {
    return (
      <div className="py-12 text-center space-y-4">
        <h2 className="text-2xl font-bold text-text-primary">Course Not Found</h2>
        <p className="text-sm text-text-secondary max-w-md mx-auto">
          We could not locate a course matching slug "<span className="font-mono text-accent-violet">{slug}</span>".
        </p>
        <Link to="/explore">
          <Button variant="primary" size="md" leftIcon={<Compass className="w-4 h-4" />}>
            Back to Course Catalog
          </Button>
        </Link>
      </div>
    )
  }

  const toggleModule = (modId: string) => {
    setExpandedModules((prev) => ({
      ...prev,
      [modId]: !prev[modId]
    }))
  }

  const handleStartLessonPreview = (lessonTitle: string) => {
    setPreviewLessonTitle(lessonTitle)
    setPreviewModalOpen(true)
  }

  const getActivityIcon = (type: ActivityType) => {
    switch (type) {
      case 'code_exercise':
        return <Terminal className="w-3.5 h-3.5 text-accent-violet" />
      case 'conversation':
        return <MessageSquare className="w-3.5 h-3.5 text-accent-cyan" />
      case 'quiz':
        return <FileQuestion className="w-3.5 h-3.5 text-state-warning" />
      default:
        return <Layers className="w-3.5 h-3.5 text-text-muted" />
    }
  }

  const getActivityLabel = (type: ActivityType) => {
    switch (type) {
      case 'code_exercise':
        return 'Code Exercise'
      case 'conversation':
        return 'Dialogue Simulation'
      case 'quiz':
        return 'Checkpoint Quiz'
      case 'practical_task':
        return 'Practical Task'
      case 'reading':
        return 'Conceptual Reading'
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Breadcrumb Back Link */}
      <div>
        <Link
          to="/explore"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Course Catalog</span>
        </Link>
      </div>

      {/* Course Hero Banner */}
      <Card variant="elevated" className="relative overflow-hidden border-border-medium p-6 sm:p-8">
        <div className="absolute top-0 right-0 w-96 h-96 bg-accent-violet/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
          <div className="space-y-4 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="cyan" size="sm">
                {course.categoryName}
              </Badge>
              <span className="text-xs font-mono text-text-muted px-2.5 py-0.5 rounded bg-bg-surface border border-border-subtle">
                {course.level} Level
              </span>
              <span className="text-xs font-mono text-text-muted flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {course.estimatedHours} hours total
              </span>
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
              {course.title}
            </h1>

            <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
              {course.fullDescription}
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Skills Taught:
              </span>
              {course.skillsTaught.map((skill) => (
                <span
                  key={skill}
                  className="text-xs font-mono px-2.5 py-1 rounded-md bg-bg-surface text-text-primary border border-border-subtle"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Primary Action Box */}
          <div className="lg:w-72 shrink-0 p-5 rounded-xl bg-bg-surface border border-border-medium space-y-4">
            <div>
              <p className="text-xs uppercase font-mono text-text-muted tracking-wider">
                Curriculum Structure
              </p>
              <p className="text-lg font-bold text-text-primary mt-1">
                {course.modulesCount} Modules • {course.lessonsCount} Lessons
              </p>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              leftIcon={<Play className="w-4 h-4 fill-current" />}
              onClick={() =>
                handleStartLessonPreview(
                  course.modules[0]?.lessons[0]?.title || 'First Lesson'
                )
              }
            >
              Start Course Preview
            </Button>

            <div className="flex items-start gap-2 text-[11px] text-text-muted leading-tight">
              <Sparkles className="w-3.5 h-3.5 text-accent-cyan shrink-0 mt-0.5" />
              <span>
                Phase 1 interactive preview mode. No account registration or backend enrollment required.
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Learning Objectives Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
          <span>What You Will Practice & Achieve</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {course.learningObjectives.map((obj, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-bg-elevated border border-border-subtle flex items-start gap-3"
            >
              <CheckCircle2 className="w-5 h-5 text-state-success shrink-0 mt-0.5" />
              <p className="text-xs sm:text-sm text-text-secondary leading-normal">
                {obj}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Module and Lesson Outline */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Chapter & Lesson Outline</h2>
            <p className="text-xs text-text-secondary">Expand modules to inspect individual learning activities</p>
          </div>
          <span className="text-xs font-mono text-text-muted">
            {course.modules.length} Modules
          </span>
        </div>

        <div className="space-y-3">
          {course.modules.map((module) => {
            const isExpanded = Boolean(expandedModules[module.id])
            return (
              <Card
                key={module.id}
                variant="elevated"
                className="p-0 overflow-hidden border-border-medium"
              >
                {/* Module Header Button */}
                <button
                  type="button"
                  onClick={() => toggleModule(module.id)}
                  aria-expanded={isExpanded}
                  className="w-full p-4 sm:p-5 flex items-center justify-between gap-4 text-left hover:bg-bg-surface/50 transition-colors cursor-pointer select-none"
                >
                  <div className="space-y-1">
                    <span className="text-xs font-mono text-accent-violet font-semibold">
                      Chapter {module.sortOrder}
                    </span>
                    <h3 className="text-base font-bold text-text-primary">
                      {module.title}
                    </h3>
                    <p className="text-xs text-text-secondary">
                      {module.description}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs font-mono text-text-muted hidden sm:inline-block">
                      {module.lessons.length} lessons
                    </span>
                    <div className="p-1 rounded-md bg-bg-surface text-text-muted">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </button>

                {/* Lessons List inside Module */}
                {isExpanded && (
                  <div className="border-t border-border-subtle bg-bg-inset/40 divide-y divide-border-subtle/50">
                    {module.lessons.map((lesson, lIdx) => (
                      <div
                        key={lesson.id}
                        className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-bg-surface/30 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <span className="w-6 h-6 rounded-md bg-bg-surface text-text-muted text-xs font-mono flex items-center justify-center shrink-0">
                            {lIdx + 1}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-xs sm:text-sm font-semibold text-text-primary">
                                {lesson.title}
                              </h4>
                            </div>
                            <p className="text-xs text-text-secondary mt-0.5 max-w-xl">
                              {lesson.description}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0 pl-9 sm:pl-0">
                          <span
                            className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-md bg-bg-surface border border-border-subtle text-text-secondary"
                            title={`Activity Type: ${getActivityLabel(lesson.activityType)}`}
                          >
                            {getActivityIcon(lesson.activityType)}
                            <span>{getActivityLabel(lesson.activityType)}</span>
                          </span>

                          <span className="text-xs font-mono text-text-muted">
                            {lesson.estimatedMinutes}m
                          </span>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStartLessonPreview(lesson.title)}
                          >
                            Preview
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      </div>

      {/* Interactive Lesson Preview Modal */}
      <Modal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        title={`Lesson Preview: ${previewLessonTitle}`}
        description="Phase 1 Lesson Workspace Simulation"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-accent-violet/10 border border-accent-violet/25 flex items-start gap-2.5 text-xs text-text-secondary">
            <Info className="w-4 h-4 text-accent-violet shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-text-primary">Phase 1 Demonstration Workspace</p>
              <p className="text-[11px] mt-0.5">
                Full course enrollment API, isolated Docker code sandbox execution, and AI tutoring are scheduled for Phase 3, Phase 5, and Phase 8 respectively. This preview shows the planned lesson briefing and interactive workspace structure.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-bg-base border border-border-subtle space-y-3">
            <h3 className="text-sm font-bold text-text-primary">
              Instructional Briefing & Objectives
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              In this chapter, you study structural requirements before writing any markup. Ensure all inputs are explicitly tied to label elements using the <code className="text-accent-cyan bg-bg-surface px-1 py-0.5 rounded font-mono">for</code> / <code className="text-accent-cyan bg-bg-surface px-1 py-0.5 rounded font-mono">id</code> attributes, and define clear validation boundaries.
            </p>

            <div className="p-3 rounded-lg bg-bg-inset border border-border-subtle font-mono text-xs text-text-secondary space-y-1">
              <div className="text-text-muted">// Starter Workspace Snippet</div>
              <div className="text-accent-violet">&lt;form aria-labelledby="form-title"&gt;</div>
              <div className="pl-4 text-text-primary">&lt;label for="username"&gt;Learner Identifier&lt;/label&gt;</div>
              <div className="pl-4 text-text-primary">&lt;input id="username" type="text" required minlength="3" /&gt;</div>
              <div className="text-accent-violet">&lt;/form&gt;</div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-border-subtle">
            <span className="text-xs font-mono text-text-muted">
              Status: Ready for Phase 5 Assessment Engine
            </span>
            <Button variant="primary" size="sm" onClick={() => setPreviewModalOpen(false)}>
              Close Preview
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
