import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { AlertCircle, RefreshCw, Compass, ArrowLeft, BookOpen, Play } from 'lucide-react'
import type { ApiCourseDetail, ApiLessonDetail } from '../../types/catalog'
import type { FlattenedLesson } from '../../types/lesson'
import { courseApi } from '../../services/courseApi'
import { LessonWorkspaceHeader } from './LessonWorkspaceHeader'
import { LessonSidebar } from './LessonSidebar'
import { LessonContent } from './LessonContent'
import { Button } from '../../components/ui/Button'

export const LessonWorkspace: React.FC = () => {
  const { courseSlug, lessonSlug } = useParams<{ courseSlug: string; lessonSlug?: string }>()
  const navigate = useNavigate()

  const [course, setCourse] = useState<ApiCourseDetail | null>(null)
  const [currentLesson, setCurrentLesson] = useState<ApiLessonDetail | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<{ message: string; isNotFound?: boolean } | null>(null)
  const [isDemo, setIsDemo] = useState<boolean>(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false)

  // Keep reference to abort controller for stale response protection
  const abortControllerRef = useRef<AbortController | null>(null)
  const mainContentRef = useRef<HTMLElement | null>(null)

  // 1. Flatten all lessons across sorted modules
  const { flattenedLessons, lessonIndexMap } = useMemo(() => {
    if (!course) return { flattenedLessons: [], lessonIndexMap: new Map<string, number>() }

    const flat: FlattenedLesson[] = []
    const indexMap = new Map<string, number>()

    const sortedModules = [...course.modules].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))

    sortedModules.forEach((mod) => {
      const sortedLessons = [...mod.lessons].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
      sortedLessons.forEach((les) => {
        const item: FlattenedLesson = {
          id: les.id,
          slug: les.slug,
          title: les.title,
          description: les.description,
          moduleId: mod.id,
          moduleTitle: mod.title,
          moduleOrder: mod.sort_order,
          sortOrder: les.sort_order,
          estimatedMinutes: les.estimated_minutes,
          globalIndex: flat.length,
        }
        indexMap.set(les.slug, flat.length)
        flat.push(item)
      })
    })

    return { flattenedLessons: flat, lessonIndexMap: indexMap }
  }, [course])

  // 2. Fetch course details and lesson content
  const loadData = useCallback(async () => {
    if (!courseSlug) return

    // Cancel in-flight request to prevent race conditions
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const controller = new AbortController()
    abortControllerRef.current = controller

    setLoading(true)
    setError(null)

    try {
      let courseData: ApiCourseDetail | null = null
      let fromDemo = false

      // Try fetching published course from backend
      try {
        courseData = await courseApi.getPublishedCourse(courseSlug, controller.signal)
      } catch (err: unknown) {
        if (controller.signal.aborted) return

        const apiErr = err as { status?: number; message?: string }
        // If 404, check if this is an explicit demo course
        if (apiErr.status === 404) {
          const demoFallback = courseApi.getDemoCourse(courseSlug)
          if (demoFallback) {
            courseData = demoFallback
            fromDemo = true
          } else {
            setError({ message: `Course "${courseSlug}" could not be found.`, isNotFound: true })
            setLoading(false)
            return
          }
        } else {
          // Genuine backend error: network down, 500, etc. Do NOT mask with demo data!
          setError({
            message: apiErr.message || 'Unable to connect to the SkillVerse learning service.',
          })
          setLoading(false)
          return
        }
      }

      if (!courseData || controller.signal.aborted) return

      setCourse(courseData)
      setIsDemo(fromDemo)

      // Determine target lesson slug
      let activeLessonSlug = lessonSlug

      // If no lesson slug provided in URL, redirect to first lesson of course
      if (!activeLessonSlug) {
        const firstModule = courseData.modules?.[0]
        const firstLesson = firstModule?.lessons?.[0]
        if (firstLesson) {
          navigate(`/learn/${courseSlug}/${firstLesson.slug}`, { replace: true })
          return
        } else {
          setError({ message: 'This course has no published lessons available.' })
          setLoading(false)
          return
        }
      }

      // Check if target lesson exists in course outline
      let foundLessonOutline: ApiLessonDetail | null = null
      for (const mod of courseData.modules) {
        const matching = mod.lessons.find((l) => l.slug === activeLessonSlug)
        if (matching) {
          foundLessonOutline = matching
          break
        }
      }

      if (!foundLessonOutline) {
        // If not in the backend course, check if it exists in the demo course outline
        const demoCourse = courseApi.getDemoCourse(courseSlug)
        if (demoCourse) {
          for (const mod of demoCourse.modules) {
            const matching = mod.lessons.find((l) => l.slug === activeLessonSlug)
            if (matching) {
              setCourse(demoCourse)
              setIsDemo(true)
              setCurrentLesson(matching)
              setLoading(false)
              return
            }
          }
        }

        setError({
          message: `Lesson "${activeLessonSlug}" is not part of course "${courseData.title}".`,
          isNotFound: true,
        })
        setLoading(false)
        return
      }

      // If demo mode, use the blocks already prepared on the demo course outline
      if (fromDemo) {
        setCurrentLesson(foundLessonOutline)
        setLoading(false)
        return
      }

      // Fetch lesson blocks from backend
      try {
        const lessonDetail = await courseApi.getPublishedLesson(
          courseSlug,
          activeLessonSlug,
          controller.signal
        )
        if (!controller.signal.aborted) {
          setCurrentLesson(lessonDetail)
          setLoading(false)
        }
      } catch (err: unknown) {
        if (controller.signal.aborted) return
        const apiErr = err as { message?: string }
        // Fall back to outline if available, otherwise show error
        if (foundLessonOutline.blocks && foundLessonOutline.blocks.length > 0) {
          setCurrentLesson(foundLessonOutline)
          setLoading(false)
        } else {
          setError({ message: apiErr.message || 'Failed to load lesson content blocks.' })
          setLoading(false)
        }
      }
    } catch (err: unknown) {
      if (controller.signal.aborted) return
      const e = err as Error
      setError({ message: e.message || 'An unexpected error occurred while loading the workspace.' })
      setLoading(false)
    }
  }, [courseSlug, lessonSlug, navigate])

  useEffect(() => {
    loadData()
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [loadData])

  // Reset scroll position to top when switching lessons
  useEffect(() => {
    if (mainContentRef.current) {
      mainContentRef.current.scrollTop = 0
    }
  }, [lessonSlug])

  // 3. Compute Navigation Context
  const currentIndex = lessonSlug ? (lessonIndexMap.get(lessonSlug) ?? -1) : -1
  const prevLesson = currentIndex > 0 ? flattenedLessons[currentIndex - 1] : null
  const nextLesson =
    currentIndex >= 0 && currentIndex < flattenedLessons.length - 1
      ? flattenedLessons[currentIndex + 1]
      : null

  const currentModuleTitle = useMemo(() => {
    if (!course || !currentLesson) return undefined
    for (const mod of course.modules) {
      if (mod.lessons.some((l) => l.slug === currentLesson.slug)) {
        return mod.title
      }
    }
    return undefined
  }, [course, currentLesson])

  // 4. Keyboard Navigation (ArrowLeft: Previous, ArrowRight: Next)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when user is typing in an input or textarea
      const target = e.target as HTMLElement | null
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return
      }

      if (e.key === 'ArrowLeft' && prevLesson) {
        e.preventDefault()
        navigate(`/learn/${courseSlug}/${prevLesson.slug}`)
      } else if (e.key === 'ArrowRight' && nextLesson) {
        e.preventDefault()
        navigate(`/learn/${courseSlug}/${nextLesson.slug}`)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [courseSlug, prevLesson, nextLesson, navigate])

  // ── Render States ────────────────────────────────────────────────────────

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-bg-base text-text-primary flex flex-col font-sans">
        {/* Skeleton Header */}
        <div className="h-16 bg-bg-elevated/80 border-b border-border-medium px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-24 h-5 rounded bg-bg-surface animate-pulse" />
            <div className="w-48 h-5 rounded bg-bg-surface animate-pulse hidden sm:block" />
          </div>
          <div className="w-20 h-6 rounded bg-bg-surface animate-pulse" />
        </div>

        {/* Skeleton Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Skeleton Sidebar */}
          <div className="w-80 bg-bg-elevated border-r border-border-medium p-4 space-y-4 hidden lg:block">
            <div className="w-32 h-4 rounded bg-bg-surface animate-pulse" />
            <div className="space-y-2 pt-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="w-full h-8 rounded bg-bg-surface/60 animate-pulse" />
              ))}
            </div>
          </div>

          {/* Skeleton Content */}
          <main className="flex-1 p-8 max-w-4xl mx-auto space-y-6">
            <div className="w-32 h-4 rounded bg-bg-surface animate-pulse" />
            <div className="w-3/4 h-8 rounded bg-bg-surface animate-pulse" />
            <div className="w-full h-24 rounded-xl bg-bg-surface/50 animate-pulse" />
            <div className="space-y-3 pt-4">
              <div className="w-full h-4 rounded bg-bg-surface/70 animate-pulse" />
              <div className="w-5/6 h-4 rounded bg-bg-surface/70 animate-pulse" />
              <div className="w-4/6 h-4 rounded bg-bg-surface/70 animate-pulse" />
            </div>
          </main>
        </div>
      </div>
    )
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-bg-base text-text-primary flex flex-col font-sans">
        <header className="h-16 bg-bg-elevated border-b border-border-medium px-6 flex items-center">
          <Link
            to="/explore"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-text-primary"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Course Catalog</span>
          </Link>
        </header>

        <main className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-md w-full text-center space-y-4 p-8 rounded-2xl bg-bg-elevated border border-border-medium shadow-xl">
            <div className="w-12 h-12 rounded-full bg-state-error/10 text-state-error mx-auto flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>

            <h2 className="text-xl font-bold text-text-primary">
              {error.isNotFound ? 'Lesson Not Found' : 'Workspace Error'}
            </h2>

            <p className="text-sm text-text-secondary">{error.message}</p>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              {error.isNotFound && courseSlug && (
                <Link to={`/learn/${courseSlug}`}>
                  <Button
                    variant="primary"
                    size="md"
                    leftIcon={<Play className="w-4 h-4 fill-current" />}
                  >
                    Start from Beginning
                  </Button>
                </Link>
              )}

              {!error.isNotFound && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={loadData}
                  leftIcon={<RefreshCw className="w-4 h-4" />}
                >
                  Retry Request
                </Button>
              )}

              {courseSlug && (
                <Link to={`/courses/${courseSlug}`}>
                  <Button variant="outline" size="md" leftIcon={<BookOpen className="w-4 h-4" />}>
                    Course Syllabus
                  </Button>
                </Link>
              )}

              <Link to="/explore">
                <Button variant="ghost" size="md" leftIcon={<Compass className="w-4 h-4" />}>
                  Catalog
                </Button>
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!course || !currentLesson) {
    return null
  }

  // Loaded Workspace
  return (
    <div className="min-h-screen bg-bg-base text-text-primary flex flex-col font-sans selection:bg-accent-violet/30 selection:text-text-primary">
      {/* Workspace Header */}
      <LessonWorkspaceHeader
        courseTitle={course.title}
        courseSlug={course.slug}
        moduleTitle={currentModuleTitle}
        lessonTitle={currentLesson.title}
        versionNumber={course.version_number}
        isDemo={isDemo}
        currentIndex={currentIndex}
        totalLessons={flattenedLessons.length}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* Main Workspace Workspace Body: Sidebar + Scrollable Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Collapsible / Responsive Module & Lesson Sidebar */}
        <LessonSidebar
          courseSlug={course.slug}
          modules={course.modules}
          currentLessonSlug={currentLesson.slug}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Scrollable Lesson Reading Content */}
        <main
          id="lesson-main-content"
          ref={mainContentRef}
          tabIndex={-1}
          className="flex-1 overflow-y-auto focus:outline-none"
        >
          <LessonContent
            lesson={currentLesson}
            courseSlug={course.slug}
            moduleTitle={currentModuleTitle}
            prevLesson={prevLesson}
            nextLesson={nextLesson}
          />
        </main>
      </div>
    </div>
  )
}
