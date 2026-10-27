import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Eye,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  Settings,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react'
import { creatorApi } from '../services/creatorApi'
import type { ApiCourseDetail, ApiLessonDetail } from '../types/catalog'
import type { ActivityAuthoring, CoursePublishResponse } from '../types/creator'
import { CurriculumTree } from '../features/creator/CurriculumTree'
import { CourseMetadataEditor } from '../features/creator/CourseMetadataEditor'
import { LessonBlocksEditor } from '../features/creator/LessonBlocksEditor'
import { ActivityAuthoringPanel } from '../features/creator/activities/ActivityAuthoringPanel'
import { ValidationPanel } from '../features/creator/ValidationPanel'
import { PublishModal } from '../features/creator/PublishModal'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'

type ActiveTab = 'metadata' | 'blocks' | 'activities' | 'validation'

interface SkillOption {
  id: string
  name: string
  slug: string
}

export const CourseEditorPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>()

  const [course, setCourse] = useState<ApiCourseDetail | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedLesson, setSelectedLesson] = useState<ApiLessonDetail | null>(null)
  const [activeTab, setActiveTab] = useState<ActiveTab>('metadata')

  const [availableSkills, setAvailableSkills] = useState<SkillOption[]>([])
  const [isPublishModalOpen, setIsPublishModalOpen] = useState<boolean>(false)
  const [publishSuccessBanner, setPublishSuccessBanner] = useState<CoursePublishResponse | null>(null)

  // 1. Fetch Course Draft and Skills Lookup
  const loadCourseDraft = useCallback(async (keepSelectedLessonId?: string) => {
    if (!courseId) return

    setLoading(true)
    setError(null)
    try {
      const [courseData, skillsData] = await Promise.all([
        creatorApi.getDraft(courseId),
        creatorApi.listSkills().catch(() => []),
      ])

      setCourse(courseData)
      setAvailableSkills(skillsData)

      // Re-resolve selected lesson if target requested or already selected
      const targetLessonId = keepSelectedLessonId || selectedLesson?.id
      if (targetLessonId && courseData.modules) {
        for (const mod of courseData.modules) {
          const matching = mod.lessons.find((l) => l.id === targetLessonId)
          if (matching) {
            setSelectedLesson(matching)
            break
          }
        }
      } else if (!selectedLesson && courseData.modules?.length > 0 && courseData.modules[0].lessons?.length > 0) {
        // Auto-select first lesson if none selected
        setSelectedLesson(courseData.modules[0].lessons[0])
        setActiveTab('blocks')
      }
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to load course draft.')
    } finally {
      setLoading(false)
    }
  }, [courseId, selectedLesson])

  useEffect(() => {
    loadCourseDraft()
  }, [loadCourseDraft])

  const handleSelectLesson = (lesson: ApiLessonDetail) => {
    setSelectedLesson(lesson)
    if (activeTab === 'metadata') {
      setActiveTab('blocks')
    }
  }

  const handleLessonSaved = () => {
    if (courseId && selectedLesson) {
      loadCourseDraft(selectedLesson.id)
    }
  }

  const handlePublished = (result: CoursePublishResponse) => {
    setPublishSuccessBanner(result)
    loadCourseDraft(selectedLesson?.id)
  }

  // ── Render States ────────────────────────────────────────────────────────

  if (loading && !course) {
    return (
      <div className="min-h-screen bg-bg-base text-text-primary flex flex-col items-center justify-center p-6">
        <RefreshCw className="w-8 h-8 text-accent-violet animate-spin mb-4" />
        <p className="text-sm text-text-muted">Loading course authoring workspace...</p>
      </div>
    )
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-bg-base text-text-primary flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full text-center space-y-4 p-8 rounded-2xl bg-bg-surface border border-border-medium shadow-xl">
          <div className="w-12 h-12 rounded-full bg-state-error/10 text-state-error mx-auto flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-text-primary">Authoring Error</h2>
          <p className="text-sm text-text-secondary">{error || 'Course not found or access denied.'}</p>
          <div className="pt-2 flex justify-center gap-3">
            <Link to="/creator">
              <Button variant="primary" size="md" leftIcon={<ArrowLeft className="w-4 h-4" />}>
                Back to Creator Studio
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const isCoursePublished = course.status === 'PUBLISHED'
  const lessonActivities = ((selectedLesson?.activities || []) as unknown) as ActivityAuthoring[]

  return (
    <div className="min-h-screen bg-bg-base text-text-primary flex flex-col font-sans">
      {/* ── Top Workspace Header ───────────────────────────────────────── */}
      <header className="h-16 shrink-0 bg-bg-elevated/90 backdrop-blur-md border-b border-border-medium px-4 sm:px-6 flex items-center justify-between gap-4 z-20">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            to="/creator"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors py-1.5 px-2 rounded-md hover:bg-bg-surface"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Studio</span>
          </Link>

          <span className="text-border-medium hidden sm:inline">•</span>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-bold text-text-primary truncate" title={course.title}>
                {course.title}
              </h1>
              {isCoursePublished ? (
                <Badge variant="emerald" size="sm">
                  Published v{course.version_number || 1}
                </Badge>
              ) : (
                <Badge variant="amber" size="sm">
                  Draft v0
                </Badge>
              )}
            </div>
            <p className="text-[11px] font-mono text-text-muted truncate">
              /{course.slug}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <Link to={`/creator/courses/${course.id}/preview`} target="_blank" rel="noreferrer">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Eye className="w-3.5 h-3.5" />}
              title="Preview interactive draft without altering learner progress"
            >
              <span className="hidden sm:inline">Preview Draft</span>
            </Button>
          </Link>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsPublishModalOpen(true)}
            leftIcon={<UploadCloud className="w-3.5 h-3.5" />}
          >
            Publish
          </Button>
        </div>
      </header>

      {/* ── Optional Publication Success Banner ───────────────────────── */}
      {publishSuccessBanner && (
        <div className="bg-emerald-500/15 border-b border-emerald-500/30 px-6 py-3 flex items-center justify-between text-xs text-emerald-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>
              Course successfully published as immutable version <strong>v{publishSuccessBanner.version_number}</strong>!
            </span>
          </div>
          <button
            type="button"
            onClick={() => setPublishSuccessBanner(null)}
            className="text-emerald-400 hover:text-emerald-300 font-bold ml-4"
          >
            ×
          </button>
        </div>
      )}

      {/* ── Main Authoring Layout: Left Curriculum Tree + Right Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Curriculum Sidebar */}
        <div className="w-80 shrink-0 bg-bg-surface border-r border-border-medium flex flex-col overflow-hidden">
          <div className="p-3 border-b border-border-subtle flex items-center justify-between bg-bg-elevated/40">
            <button
              type="button"
              onClick={() => {
                setSelectedLesson(null)
                setActiveTab('metadata')
              }}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                !selectedLesson
                  ? 'bg-accent-violet/15 text-accent-violet'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Course Settings & Metadata</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            <CurriculumTree
              course={course}
              selectedLessonId={selectedLesson?.id || null}
              onSelectLesson={handleSelectLesson}
              onRefreshCourse={() => loadCourseDraft(selectedLesson?.id)}
            />
          </div>
        </div>

        {/* Right Authoring Content & Workspace */}
        <main className="flex-1 flex flex-col overflow-hidden bg-bg-base">
          {/* Subheader / Tabs */}
          <div className="h-12 shrink-0 bg-bg-surface border-b border-border-subtle px-6 flex items-center justify-between">
            <div className="flex items-center gap-1 sm:gap-2">
              {selectedLesson ? (
                <>
                  <button
                    type="button"
                    onClick={() => setActiveTab('blocks')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                      activeTab === 'blocks'
                        ? 'bg-accent-violet text-white shadow-xs'
                        : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                    }`}
                  >
                    Content Blocks
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('activities')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                      activeTab === 'activities'
                        ? 'bg-accent-violet text-white shadow-xs'
                        : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                    }`}
                  >
                    <span>Activities</span>
                    {lessonActivities.length > 0 && (
                      <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-bg-elevated text-text-primary">
                        {lessonActivities.length}
                      </span>
                    )}
                  </button>
                </>
              ) : null}

              <button
                type="button"
                onClick={() => setActiveTab('metadata')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  activeTab === 'metadata'
                    ? 'bg-accent-violet text-white shadow-xs'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                }`}
              >
                Course Metadata
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('validation')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'validation'
                    ? 'bg-accent-violet text-white shadow-xs'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Pre-Publish Validation</span>
              </button>
            </div>

            {selectedLesson && (
              <div className="hidden md:flex items-center gap-2 text-xs text-text-muted">
                <FileText className="w-3.5 h-3.5 text-accent-cyan" />
                <span className="font-medium text-text-primary truncate max-w-xs">
                  {selectedLesson.title}
                </span>
              </div>
            )}
          </div>

          {/* Tab Body */}
          <div className="flex-1 overflow-y-auto p-6 sm:p-8">
            <div className="max-w-4xl mx-auto">
              {activeTab === 'metadata' && (
                <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-xs">
                  <CourseMetadataEditor
                    course={course}
                    availableSkills={availableSkills}
                    onSaved={() => loadCourseDraft(selectedLesson?.id)}
                  />
                </div>
              )}

              {activeTab === 'blocks' && selectedLesson && (
                <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-xs">
                  <LessonBlocksEditor
                    courseId={course.id}
                    lessonId={selectedLesson.id}
                    lessonTitle={selectedLesson.title}
                    initialBlocks={
                      (selectedLesson.blocks || []).map((b) => ({
                        id: b.id,
                        type: b.block_type,
                        data: (b.content || {}) as Record<string, unknown>,
                      }))
                    }
                    onSaved={handleLessonSaved}
                  />
                </div>
              )}

              {activeTab === 'activities' && selectedLesson && (
                <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-xs">
                  <ActivityAuthoringPanel
                    lessonId={selectedLesson.id}
                    lessonTitle={selectedLesson.title}
                    activities={lessonActivities}
                    courseSkills={course.skills}
                    onActivitiesChanged={() => loadCourseDraft(selectedLesson.id)}
                  />
                </div>
              )}

              {activeTab === 'validation' && (
                <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-xs">
                  <ValidationPanel
                    courseId={course.id}
                    onJumpToLesson={(lessonId) => {
                      if (course.modules) {
                        for (const mod of course.modules) {
                          const matching = mod.lessons.find((l) => l.id === lessonId)
                          if (matching) {
                            setSelectedLesson(matching)
                            setActiveTab('blocks')
                            break
                          }
                        }
                      }
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* ── Publication Modal ─────────────────────────────────────────── */}
      <PublishModal
        courseId={course.id}
        courseSlug={course.slug}
        courseTitle={course.title}
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        onPublished={handlePublished}
      />
    </div>
  )
}
