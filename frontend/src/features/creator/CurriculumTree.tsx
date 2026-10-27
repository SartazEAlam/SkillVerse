import React, { useState } from 'react'
import {
  Folder,
  FileText,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Edit2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import type { ApiCourseDetail, ApiModuleOutline, ApiLessonDetail } from '../../types/catalog'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface CurriculumTreeProps {
  course: ApiCourseDetail
  selectedLessonId: string | null
  onSelectLesson: (lesson: ApiLessonDetail, module: ApiModuleOutline) => void
  onRefreshCourse: () => void
}

export const CurriculumTree: React.FC<CurriculumTreeProps> = ({
  course,
  selectedLessonId,
  onSelectLesson,
  onRefreshCourse,
}) => {
  const [expandedModules, setExpandedModules] = useState<Set<string>>(
    new Set(course.modules.map((m) => m.id))
  )
  const [newModuleTitle, setNewModuleTitle] = useState<string>('')
  const [showAddModule, setShowAddModule] = useState<boolean>(false)

  const [addingLessonModuleId, setAddingLessonModuleId] = useState<string | null>(null)
  const [newLessonTitle, setNewLessonTitle] = useState<string>('')
  const [newLessonSlug, setNewLessonSlug] = useState<string>('')

  const [editingModuleId, setEditingModuleId] = useState<string | null>(null)
  const [editModuleTitle, setEditModuleTitle] = useState<string>('')

  const [busy, setBusy] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const toggleExpand = (modId: string) => {
    setExpandedModules((prev) => {
      const next = new Set(prev)
      if (next.has(modId)) next.delete(modId)
      else next.add(modId)
      return next
    })
  }

  // ── Module Operations ──────────────────────────────────────────

  const handleAddModule = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newModuleTitle.trim()) return

    setBusy(true)
    setError(null)
    try {
      await creatorApi.addModule(course.id, {
        title: newModuleTitle.trim(),
        sort_order: course.modules.length,
      })
      setNewModuleTitle('')
      setShowAddModule(false)
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to add module.')
    } finally {
      setBusy(false)
    }
  }

  const handleUpdateModule = async (moduleId: string) => {
    if (!editModuleTitle.trim()) return

    setBusy(true)
    setError(null)
    try {
      await creatorApi.updateModule(course.id, moduleId, {
        title: editModuleTitle.trim(),
      })
      setEditingModuleId(null)
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to update module.')
    } finally {
      setBusy(false)
    }
  }

  const handleDeleteModule = async (moduleId: string, title: string) => {
    if (!window.confirm(`Are you sure you want to delete module "${title}" and all its lessons?`)) {
      return
    }

    setBusy(true)
    setError(null)
    try {
      await creatorApi.deleteModule(course.id, moduleId)
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to delete module.')
    } finally {
      setBusy(false)
    }
  }

  const handleMoveModule = async (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= course.modules.length) return

    const reordered = [...course.modules]
    const [moved] = reordered.splice(index, 1)
    reordered.splice(targetIndex, 0, moved)

    setBusy(true)
    try {
      await creatorApi.reorderCurriculum(course.id, {
        modules: reordered.map((m, idx) => ({ id: m.id, sort_order: idx })),
      })
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to reorder modules.')
    } finally {
      setBusy(false)
    }
  }

  // ── Lesson Operations ──────────────────────────────────────────

  const handleAddLesson = async (moduleId: string, e: React.FormEvent) => {
    e.preventDefault()
    if (!newLessonTitle.trim() || !newLessonSlug.trim()) return

    setBusy(true)
    setError(null)
    try {
      const mod = course.modules.find((m) => m.id === moduleId)
      await creatorApi.addLesson(course.id, moduleId, {
        title: newLessonTitle.trim(),
        slug: newLessonSlug.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        sort_order: mod?.lessons?.length || 0,
      })
      setNewLessonTitle('')
      setNewLessonSlug('')
      setAddingLessonModuleId(null)
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to add lesson.')
    } finally {
      setBusy(false)
    }
  }

  const handleDeleteLesson = async (lessonId: string, title: string) => {
    if (!window.confirm(`Are you sure you want to delete lesson "${title}"?`)) {
      return
    }

    setBusy(true)
    setError(null)
    try {
      await creatorApi.deleteLesson(course.id, lessonId)
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to delete lesson.')
    } finally {
      setBusy(false)
    }
  }

  const handleMoveLesson = async (
    mod: ApiModuleOutline,
    lessonIndex: number,
    direction: 'up' | 'down'
  ) => {
    const targetIndex = direction === 'up' ? lessonIndex - 1 : lessonIndex + 1
    if (targetIndex < 0 || targetIndex >= mod.lessons.length) return

    const reordered = [...mod.lessons]
    const [moved] = reordered.splice(lessonIndex, 1)
    reordered.splice(targetIndex, 0, moved)

    setBusy(true)
    try {
      await creatorApi.reorderCurriculum(course.id, {
        lessons: reordered.map((l, idx) => ({ id: l.id, sort_order: idx })),
      })
      onRefreshCourse()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to reorder lessons.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Curriculum title & Add Module button */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Curriculum Structure
          </h3>
          <span className="text-[11px] text-slate-500">
            {course.modules.length} Modules &bull;{' '}
            {course.modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0)} Lessons
          </span>
        </div>

        <button
          type="button"
          onClick={() => setShowAddModule(true)}
          className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Module
        </button>
      </div>

      {error && (
        <div className="p-2.5 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300 text-xs">
          {error}
        </div>
      )}

      {/* Add Module Inline Form */}
      {showAddModule && (
        <form
          onSubmit={handleAddModule}
          className="p-3 bg-slate-900 border border-indigo-500/50 rounded-xl space-y-2 animate-fade-in"
        >
          <label className="block text-xs font-semibold text-slate-300">New Module Title</label>
          <input
            type="text"
            value={newModuleTitle}
            onChange={(e) => setNewModuleTitle(e.target.value)}
            placeholder="e.g. Module 1: Core Fundamentals"
            className="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            autoFocus
            required
          />
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setShowAddModule(false)}
              className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <Button type="submit" size="sm" disabled={busy} className="text-xs py-1">
              Add Module
            </Button>
          </div>
        </form>
      )}

      {/* Modules list */}
      {course.modules.length === 0 ? (
        <div className="p-6 text-center bg-slate-900/30 border border-slate-800 border-dashed rounded-xl">
          <Folder className="w-6 h-6 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-400">No curriculum modules created yet.</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowAddModule(true)}
            className="mt-3 text-xs"
          >
            Create First Module
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {course.modules.map((mod, modIdx) => {
            const isExpanded = expandedModules.has(mod.id)
            const isEditing = editingModuleId === mod.id

            return (
              <div
                key={mod.id}
                className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden transition-all"
              >
                {/* Module header */}
                <div className="flex items-center justify-between p-2.5 bg-slate-850/60 border-b border-slate-800/60">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <button
                      type="button"
                      onClick={() => toggleExpand(mod.id)}
                      className="p-1 text-slate-400 hover:text-slate-200 rounded"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>

                    <Folder className="w-4 h-4 text-indigo-400 shrink-0" />

                    {isEditing ? (
                      <div className="flex items-center gap-1.5 flex-1">
                        <input
                          type="text"
                          value={editModuleTitle}
                          onChange={(e) => setEditModuleTitle(e.target.value)}
                          className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 flex-1"
                          autoFocus
                        />
                        <button
                          type="button"
                          onClick={() => handleUpdateModule(mod.id)}
                          className="text-xs text-indigo-400 font-medium px-2 py-0.5 hover:underline"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingModuleId(null)}
                          className="text-xs text-slate-400 px-1 py-0.5"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs font-semibold text-slate-200 truncate">
                        {mod.title}
                      </span>
                    )}
                  </div>

                  {!isEditing && (
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleMoveModule(modIdx, 'up')}
                        disabled={modIdx === 0 || busy}
                        className="p-1 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                        title="Move module up"
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMoveModule(modIdx, 'down')}
                        disabled={modIdx === course.modules.length - 1 || busy}
                        className="p-1 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                        title="Move module down"
                      >
                        <ArrowDown className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingModuleId(mod.id)
                          setEditModuleTitle(mod.title)
                        }}
                        className="p-1 text-slate-400 hover:text-indigo-400"
                        title="Rename module"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteModule(mod.id, mod.title)}
                        className="p-1 text-slate-400 hover:text-red-400"
                        title="Delete module"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Module lessons */}
                {isExpanded && (
                  <div className="p-2 space-y-1.5 bg-slate-950/30">
                    {mod.lessons.map((les, lesIdx) => {
                      const isSelected = selectedLessonId === les.id
                      return (
                        <div
                          key={les.id}
                          className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-all ${
                            isSelected
                              ? 'bg-indigo-600/20 border border-indigo-500/50 text-indigo-200'
                              : 'hover:bg-slate-800/60 border border-transparent text-slate-300'
                          }`}
                          onClick={() => onSelectLesson(les, mod)}
                        >
                          <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                            <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="truncate">{les.title}</span>
                          </div>

                          <div
                            className="flex items-center gap-1 shrink-0 ml-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              type="button"
                              onClick={() => handleMoveLesson(mod, lesIdx, 'up')}
                              disabled={lesIdx === 0 || busy}
                              className="p-0.5 text-slate-500 hover:text-indigo-400 disabled:opacity-20"
                            >
                              <ArrowUp className="w-2.5 h-2.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveLesson(mod, lesIdx, 'down')}
                              disabled={lesIdx === mod.lessons.length - 1 || busy}
                              className="p-0.5 text-slate-500 hover:text-indigo-400 disabled:opacity-20"
                            >
                              <ArrowDown className="w-2.5 h-2.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteLesson(les.id, les.title)}
                              className="p-0.5 text-slate-500 hover:text-red-400 transition-colors"
                              title="Delete lesson"
                            >
                              <Trash2 className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        </div>
                      )
                    })}

                    {/* Add Lesson Form */}
                    {addingLessonModuleId === mod.id ? (
                      <form
                        onSubmit={(e) => handleAddLesson(mod.id, e)}
                        className="p-2.5 bg-slate-900 border border-indigo-500/40 rounded-lg space-y-2 mt-2"
                      >
                        <input
                          type="text"
                          value={newLessonTitle}
                          onChange={(e) => {
                            setNewLessonTitle(e.target.value)
                            if (!newLessonSlug || newLessonSlug === newLessonTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-')) {
                              setNewLessonSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-'))
                            }
                          }}
                          placeholder="Lesson Title"
                          className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500"
                          autoFocus
                          required
                        />
                        <input
                          type="text"
                          value={newLessonSlug}
                          onChange={(e) => setNewLessonSlug(e.target.value)}
                          placeholder="lesson-slug"
                          className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-300 font-mono"
                          required
                        />
                        <div className="flex justify-end gap-1.5 pt-1">
                          <button
                            type="button"
                            onClick={() => setAddingLessonModuleId(null)}
                            className="px-2 py-0.5 text-[11px] text-slate-400"
                          >
                            Cancel
                          </button>
                          <Button type="submit" size="sm" disabled={busy} className="text-xs py-0.5 px-2">
                            Add Lesson
                          </Button>
                        </div>
                      </form>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setAddingLessonModuleId(mod.id)
                          setNewLessonTitle('')
                          setNewLessonSlug('')
                        }}
                        className="w-full flex items-center justify-center gap-1 py-1.5 mt-1 text-[11px] text-slate-400 hover:text-indigo-300 border border-dashed border-slate-800 hover:border-slate-700 rounded-lg transition-colors"
                      >
                        <Plus className="w-3 h-3" />
                        Add Lesson to Module
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
