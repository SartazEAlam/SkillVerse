import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Plus,
  Search,
  BookOpen,
  Layers,
  AlertCircle,
  Clock,
  Trash2,
  ExternalLink,
  Edit3,
  CheckCircle2,
  Eye,
  RefreshCw,
  FolderGit2,
  ShieldAlert,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { creatorApi } from '../services/creatorApi'
import type { ManagedCourseItem } from '../types/creator'
import type { ApiCourseDetail } from '../types/catalog'
import { CreateCourseModal } from '../features/creator/CreateCourseModal'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'

export const CreatorStudioPage: React.FC = () => {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  const [courses, setCourses] = useState<ManagedCourseItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const [searchTerm, setSearchTerm] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'>('ALL')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const isAuthorized =
    Boolean(user) &&
    (user?.role?.toLowerCase() === 'creator' || user?.role?.toLowerCase() === 'admin')

  const loadCourses = useCallback(async () => {
    if (!isAuthorized) return

    setLoading(true)
    setError(null)
    try {
      const data = await creatorApi.listManagedCourses()
      setCourses(data.courses || data.items || [])
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to load courses managed by your account.')
    } finally {
      setLoading(false)
    }
  }, [isAuthorized])

  useEffect(() => {
    if (!authLoading && isAuthorized) {
      loadCourses()
    }
  }, [authLoading, isAuthorized, loadCourses])

  const handleDeleteCourse = async (courseId: string) => {
    setDeletingId(courseId)
    setError(null)
    try {
      await creatorApi.deleteCourse(courseId)
      setCourses((prev) => prev.filter((c) => c.id !== courseId))
      setDeleteConfirmId(null)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to delete course.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleCourseCreated = (newCourse: ApiCourseDetail) => {
    setIsCreateModalOpen(false)
    // Directly navigate to the newly created course editor
    navigate(`/creator/courses/${newCourse.id}`)
  }

  // ── Authentication & Role Verification States ─────────────────────────

  if (authLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex justify-center items-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-accent-violet animate-spin" />
          <p className="text-sm text-text-muted">Verifying creator credentials...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-accent-violet/10 border border-accent-violet/30 text-accent-violet mx-auto flex items-center justify-center mb-6">
          <FolderGit2 className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-text-primary mb-3">Creator Studio</h1>
        <p className="text-text-secondary text-sm mb-6 max-w-md mx-auto">
          Please sign in to your creator account to create, structure, and publish interactive learning courses.
        </p>
        <Link to="/login">
          <Button variant="primary" size="md">
            Sign In to Continue
          </Button>
        </Link>
      </div>
    )
  }

  if (!isAuthorized) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mx-auto flex items-center justify-center mb-6">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-text-primary mb-3">Creator Access Required</h1>
        <p className="text-text-secondary text-sm mb-6 max-w-md mx-auto">
          Your current account is registered as a <span className="font-semibold text-text-primary capitalize">{user.role}</span>.
          Creator Studio is reserved for course authors and administrators.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link to="/explore">
            <Button variant="outline" size="md">
              Browse Course Catalog
            </Button>
          </Link>
          <Link to="/">
            <Button variant="primary" size="md">
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  // ── Filtered Courses ──────────────────────────────────────────────────

  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      searchTerm.trim() === '' ||
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.slug.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'DRAFT' && c.status === 'DRAFT') ||
      (statusFilter === 'PUBLISHED' && c.status === 'PUBLISHED') ||
      (statusFilter === 'ARCHIVED' && c.status === 'ARCHIVED')

    return matchesSearch && matchesStatus
  })

  const totalCourses = courses.length
  const publishedCourses = courses.filter((c) => c.status === 'PUBLISHED').length
  const draftCourses = courses.filter((c) => c.status === 'DRAFT').length

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border-medium">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-accent-cyan">
              Authoring Workspace
            </span>
            <Badge variant="violet" size="sm">
              Creator Studio
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
            Course Authoring
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Build, organize curriculum, author activities, preview drafts, and publish versioned courses.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Button
            variant="outline"
            size="md"
            onClick={loadCourses}
            disabled={loading}
            leftIcon={<RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Course
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-mono text-text-muted uppercase">Managed Courses</p>
            <p className="text-2xl font-bold text-text-primary mt-1">{totalCourses}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-accent-violet/10 text-accent-violet flex items-center justify-center">
            <BookOpen className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-mono text-text-muted uppercase">Drafts in Authoring</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">{draftCourses}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <Edit3 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-mono text-text-muted uppercase">Published Catalog</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{publishedCourses}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-state-error/10 border border-state-error/30 text-state-error text-sm flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by title or slug..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-bg-surface border border-border-subtle text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-bg-surface border border-border-subtle self-start sm:self-auto overflow-x-auto max-w-full">
          {(['ALL', 'DRAFT', 'PUBLISHED', 'ARCHIVED'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
                statusFilter === status
                  ? 'bg-accent-violet text-white shadow-xs'
                  : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
              }`}
            >
              {status === 'ALL' ? 'All Courses' : status.charAt(0) + status.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Course List / Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-64 rounded-2xl bg-bg-surface/50 border border-border-subtle p-6 space-y-4 animate-pulse"
            >
              <div className="flex justify-between">
                <div className="w-20 h-5 rounded bg-bg-elevated" />
                <div className="w-16 h-5 rounded bg-bg-elevated" />
              </div>
              <div className="w-3/4 h-6 rounded bg-bg-elevated" />
              <div className="space-y-2">
                <div className="w-full h-4 rounded bg-bg-elevated" />
                <div className="w-5/6 h-4 rounded bg-bg-elevated" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-bg-surface border border-dashed border-border-medium space-y-4">
          <div className="w-12 h-12 rounded-xl bg-bg-elevated text-text-muted mx-auto flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-text-primary">No courses found</h3>
            <p className="text-xs text-text-muted mt-1 max-w-sm mx-auto">
              {searchTerm || statusFilter !== 'ALL'
                ? 'Try adjusting your search criteria or filter options.'
                : 'Get started by creating your very first course draft.'}
            </p>
          </div>
          {!searchTerm && statusFilter === 'ALL' && (
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsCreateModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Create Course Draft
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => {
            const isDraft = course.status === 'DRAFT'
            const isPublished = course.status === 'PUBLISHED'

            return (
              <div
                key={course.id}
                className="flex flex-col justify-between rounded-2xl bg-bg-surface border border-border-subtle hover:border-border-medium transition-all shadow-xs hover:shadow-md p-5 group"
              >
                <div className="space-y-3">
                  {/* Status, Version, Difficulty Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {isDraft && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-amber-500/15 text-amber-400 border border-amber-500/30">
                          Draft (v0)
                        </span>
                      )}
                      {isPublished && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          Published v{course.published_version_number || 1}
                        </span>
                      )}
                      {course.status === 'ARCHIVED' && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
                          Archived
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold uppercase bg-bg-elevated text-text-muted border border-border-subtle">
                        {course.difficulty_level}
                      </span>
                    </div>

                    {course.has_draft && isPublished && (
                      <span
                        title="Unpublished working draft changes exist"
                        className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"
                      />
                    )}
                  </div>

                  {/* Course Title and Slug */}
                  <div>
                    <h3 className="text-base font-bold text-text-primary group-hover:text-accent-violet transition-colors line-clamp-1">
                      {course.title}
                    </h3>
                    <p className="text-[11px] font-mono text-text-muted mt-0.5 truncate">
                      /{course.slug}
                    </p>
                  </div>

                  {/* Short Description */}
                  <p className="text-xs text-text-secondary line-clamp-2 min-h-[2rem]">
                    {course.short_description || 'No description provided yet.'}
                  </p>

                  {/* Skills Pills */}
                  {course.skills && course.skills.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      {course.skills.slice(0, 3).map((sk: { id: string; name: string }) => (
                        <span
                          key={sk.id}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-accent-violet/10 text-accent-violet border border-accent-violet/20"
                        >
                          {sk.name}
                        </span>
                      ))}
                      {course.skills.length > 3 && (
                        <span className="text-[10px] text-text-muted">
                          +{course.skills.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Counts: Modules & Lessons */}
                  <div className="pt-2 border-t border-border-subtle/60 flex items-center justify-between text-xs text-text-muted">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5" />
                      {course.module_count ?? course.modules_count ?? 0} modules • {course.lesson_count ?? course.lessons_count ?? 0} lessons
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {course.estimated_duration_minutes || 60}m
                    </span>
                  </div>
                </div>

                {/* Actions Footer */}
                <div className="pt-4 mt-4 border-t border-border-subtle flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Link to={`/creator/courses/${course.id}`}>
                      <Button variant="primary" size="sm" leftIcon={<Edit3 className="w-3.5 h-3.5" />}>
                        Edit Content
                      </Button>
                    </Link>

                    <Link to={`/creator/courses/${course.id}/preview`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Preview Course Draft"
                        leftIcon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Preview
                      </Button>
                    </Link>

                    {isPublished && (
                      <Link to={`/courses/${course.slug}`} target="_blank" rel="noreferrer">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Open Published Catalog View"
                          leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
                        />
                      </Link>
                    )}
                  </div>

                  {/* Delete Course Confirm */}
                  {deleteConfirmId === course.id ? (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="destructive"
                        size="sm"
                        disabled={deletingId === course.id}
                        onClick={() => handleDeleteCourse(course.id)}
                      >
                        Confirm
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteConfirmId(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      title="Delete Course"
                      onClick={() => setDeleteConfirmId(course.id)}
                      leftIcon={<Trash2 className="w-3.5 h-3.5 text-text-muted hover:text-state-error" />}
                    />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create Course Modal */}
      <CreateCourseModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={handleCourseCreated}
      />
    </div>
  )
}
