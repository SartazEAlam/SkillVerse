import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Menu, X, Sparkles, BookOpen } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'

interface LessonWorkspaceHeaderProps {
  courseTitle: string
  courseSlug: string
  moduleTitle?: string
  lessonTitle?: string
  versionNumber?: number | null
  isDemo?: boolean
  currentIndex: number
  totalLessons: number
  onToggleSidebar: () => void
  isSidebarOpen: boolean
  isPreview?: boolean
  courseId?: string
  onToggleAITutor?: () => void
  isAITutorOpen?: boolean
}

export const LessonWorkspaceHeader: React.FC<LessonWorkspaceHeaderProps> = ({
  courseTitle,
  courseSlug,
  moduleTitle,
  lessonTitle,
  versionNumber,
  isDemo = false,
  currentIndex,
  totalLessons,
  onToggleSidebar,
  isSidebarOpen,
  isPreview = false,
  courseId,
  onToggleAITutor,
  isAITutorOpen = false,
}) => {
  return (
    <header className="h-16 shrink-0 bg-bg-elevated/90 backdrop-blur-md border-b border-border-medium px-4 sm:px-6 flex items-center justify-between gap-4 z-20">
      {/* Left: Mobile Toggle & Course Context */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label={isSidebarOpen ? 'Close curriculum navigation' : 'Open curriculum navigation'}
          aria-expanded={isSidebarOpen}
          className="lg:hidden p-2 rounded-lg bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-surface/80 border border-border-subtle focus-visible:ring-1 focus-visible:ring-accent-violet cursor-pointer"
        >
          {isSidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>

        {/* Back Link to Course Overview or Editor */}
        <Link
          to={isPreview && courseId ? `/creator/courses/${courseId}` : `/courses/${courseSlug}`}
          title={isPreview ? 'Return to Course Editor' : 'Return to Course Overview'}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors shrink-0 py-1.5 px-2 rounded-md hover:bg-bg-surface focus-visible:ring-1 focus-visible:ring-accent-violet"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">{isPreview ? 'Course Editor' : 'Course Overview'}</span>
        </Link>

        <span className="text-border-medium hidden sm:inline">•</span>

        {/* Course & Module Breadcrumbs */}
        <div className="min-w-0 flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-accent-violet/10 text-accent-violet hidden sm:flex items-center justify-center shrink-0">
            <BookOpen className="w-3.5 h-3.5" />
          </div>
          <div className="min-w-0">
            <h1 className="text-xs sm:text-sm font-bold text-text-primary truncate" title={courseTitle}>
              {courseTitle}
            </h1>
            {moduleTitle && (
              <p className="text-[11px] text-text-muted truncate hidden md:block" title={moduleTitle}>
                {moduleTitle}
                {lessonTitle ? ` › ${lessonTitle}` : ''}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Right: Version / Demo / Preview Status & Lesson Progress */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Published Version, Demo, or Draft Preview Indicator */}
        {isPreview ? (
          <Badge variant="amber" size="sm">
            <Sparkles className="w-3 h-3 mr-1" />
            Draft Preview Mode
          </Badge>
        ) : isDemo ? (
          <Badge variant="amber" size="sm" className="hidden xs:inline-flex">
            <Sparkles className="w-3 h-3 mr-1" />
            Demo Track
          </Badge>
        ) : (
          <Badge variant="violet" size="sm">
            Published v{versionNumber || 1}
          </Badge>
        )}


        {/* AI Tutor Toggle Button */}
        {onToggleAITutor && (
          <button
            type="button"
            onClick={onToggleAITutor}
            aria-label="Toggle AI Tutor companion (Alt+T)"
            aria-expanded={isAITutorOpen}
            title="Ask AI Tutor (Alt+T)"
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
              isAITutorOpen
                ? 'bg-accent-violet text-white border-accent-violet shadow-sm shadow-accent-violet/30'
                : 'bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-elevated border-border-subtle hover:border-accent-violet/30'
            }`}
          >
            <Sparkles className={`w-3.5 h-3.5 ${isAITutorOpen ? 'text-white' : 'text-accent-cyan'}`} />
            <span className="hidden sm:inline">AI Tutor</span>
          </button>
        )}

        {/* Lesson Counter */}
        {totalLessons > 0 && (
          <div
            className="text-xs font-mono text-text-muted px-2.5 py-1 rounded-md bg-bg-surface border border-border-subtle"
            aria-label={`Lesson ${currentIndex + 1} of ${totalLessons}`}
          >
            <span className="text-text-primary font-bold">{currentIndex + 1}</span>
            <span className="text-text-muted/60"> / </span>
            <span>{totalLessons}</span>
          </div>
        )}
      </div>
    </header>
  )
}
