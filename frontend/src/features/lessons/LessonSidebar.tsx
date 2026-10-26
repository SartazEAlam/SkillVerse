import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronRight, FileText, CheckCircle2, BookOpen, X } from 'lucide-react'
import type { ApiModuleDetail } from '../../types/catalog'

interface LessonSidebarProps {
  courseSlug: string
  modules: ApiModuleDetail[]
  currentLessonSlug: string
  completedLessonSlugs?: Set<string>
  isOpen: boolean
  onClose: () => void
}

export const LessonSidebar: React.FC<LessonSidebarProps> = ({
  courseSlug,
  modules,
  currentLessonSlug,
  completedLessonSlugs,
  isOpen,
  onClose,
}) => {
  // Find which module contains the active lesson
  const activeModule = modules.find((m) =>
    m.lessons.some((l) => l.slug === currentLessonSlug)
  )

  // Track expanded state of modules; default to expanding all or active module
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {}
    modules.forEach((m) => {
      initial[m.id] = true
    })
    return initial
  })

  // Ensure active module is expanded when lesson changes
  useEffect(() => {
    if (activeModule) {
      setExpandedMap((prev) => ({
        ...prev,
        [activeModule.id]: true,
      }))
    }
  }, [activeModule])

  // Handle ESC key to close mobile sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const toggleModule = (moduleId: string) => {
    setExpandedMap((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }))
  }

  const sortedModules = [...modules].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          role="presentation"
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-30 lg:hidden animate-fadeIn"
        />
      )}

      {/* Sidebar Container */}
      <nav
        aria-label="Course curriculum"
        className={`fixed lg:static top-16 bottom-0 left-0 w-80 max-w-[85vw] bg-bg-elevated border-r border-border-medium z-40 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-accent-violet" />
            <span className="text-xs font-bold uppercase tracking-wider text-text-primary">
              Curriculum Outline
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-text-muted">
              {modules.length} {modules.length === 1 ? 'Module' : 'Modules'}
            </span>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close curriculum outline"
              className="lg:hidden p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-bg-surface focus-visible:ring-1 focus-visible:ring-accent-violet cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Modules List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3 divide-y divide-border-subtle/40">
          {sortedModules.map((module, mIdx) => {
            const isExpanded = Boolean(expandedMap[module.id])
            const sortedLessons = [...module.lessons].sort(
              (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)
            )

            return (
              <div key={module.id} className={mIdx > 0 ? 'pt-3' : ''}>
                {/* Module Expand Toggle Header */}
                <button
                  type="button"
                  onClick={() => toggleModule(module.id)}
                  aria-expanded={isExpanded}
                  className="w-full flex items-center justify-between p-2 rounded-lg text-left hover:bg-bg-surface transition-colors cursor-pointer group focus-visible:ring-1 focus-visible:ring-accent-violet"
                >
                  <div className="min-w-0 pr-2">
                    <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-accent-violet block">
                      Chapter {module.sort_order || mIdx + 1}
                    </span>
                    <h3 className="text-xs font-bold text-text-primary truncate mt-0.5">
                      {module.title}
                    </h3>
                  </div>
                  <div className="text-text-muted group-hover:text-text-primary shrink-0 transition-colors">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                </button>

                {/* Lessons inside Module */}
                {isExpanded && (
                  <div className="mt-1 pl-2 space-y-1">
                    {sortedLessons.map((lesson) => {
                      const isCurrent = lesson.slug === currentLessonSlug
                      const isCompleted = completedLessonSlugs?.has(lesson.slug)

                      return (
                        <Link
                          key={lesson.id}
                          to={`/learn/${courseSlug}/${lesson.slug}`}
                          onClick={onClose}
                          aria-current={isCurrent ? 'page' : undefined}
                          className={`group flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors focus-visible:ring-1 focus-visible:ring-accent-violet ${
                            isCurrent
                              ? 'bg-accent-violet/15 text-accent-violet font-semibold border-l-2 border-accent-violet shadow-xs'
                              : isCompleted
                              ? 'text-text-primary hover:bg-bg-surface/80'
                              : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface/80'
                          }`}
                        >
                          <div className="shrink-0 mt-0.5">
                            {isCompleted ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-state-success" />
                            ) : isCurrent ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-accent-violet" />
                            ) : (
                              <FileText className="w-3.5 h-3.5 text-text-muted group-hover:text-text-secondary" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate leading-tight">{lesson.title}</p>
                            {lesson.estimated_minutes && (
                              <span className="text-[10px] font-mono text-text-muted">
                                {lesson.estimated_minutes}m
                              </span>
                            )}
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </nav>
    </>
  )
}
