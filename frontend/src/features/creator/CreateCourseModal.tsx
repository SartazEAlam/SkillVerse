import React, { useState, useEffect } from 'react'
import { X, Sparkles, AlertCircle } from 'lucide-react'
import type { ApiCourseDetail } from '../../types/catalog'
import type { CourseCreatePayload } from '../../types/creator'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface DisciplineItem {
  id: string
  slug: string
  name: string
}

interface SkillItem {
  id: string
  slug: string
  name: string
  discipline_id: string
}

interface CreateCourseModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (course: ApiCourseDetail) => void
}

export const CreateCourseModal: React.FC<CreateCourseModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [title, setTitle] = useState<string>('')
  const [slug, setSlug] = useState<string>('')
  const [shortDescription, setShortDescription] = useState<string>('')
  const [disciplineId, setDisciplineId] = useState<string>('')
  const [difficultyLevel, setDifficultyLevel] = useState<'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'>('BEGINNER')
  const [durationMinutes, setDurationMinutes] = useState<number>(120)

  const [disciplines, setDisciplines] = useState<DisciplineItem[]>([])
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([])

  const [loadingLookups, setLoadingLookups] = useState<boolean>(false)
  const [creating, setCreating] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return

    const loadLookups = async () => {
      setLoadingLookups(true)
      try {
        const [discs, sks] = await Promise.all([
          creatorApi.listDisciplines(),
          creatorApi.listSkills(),
        ])
        setDisciplines(discs)
        setDisciplineId((prev) => prev || (discs[0]?.id || ''))
        setSkills(sks)
      } catch (err: unknown) {
        console.error('Failed to load metadata lookups', err)
      } finally {
        setLoadingLookups(false)
      }
    }

    loadLookups()
  }, [isOpen])

  if (!isOpen) return null

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setTitle(val)
    if (!slug || slug === title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, -1)) {
      setSlug(
        val
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-+|-+$/g, '')
      )
    }
  }

  const handleToggleSkill = (skillId: string) => {
    setSelectedSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    )
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !slug.trim() || !shortDescription.trim() || !disciplineId) {
      setError('Please fill in all required fields.')
      return
    }

    setCreating(true)
    setError(null)

    try {
      const payload: CourseCreatePayload = {
        title: title.trim(),
        slug: slug.trim().toLowerCase(),
        short_description: shortDescription.trim(),
        discipline_id: disciplineId,
        difficulty_level: difficultyLevel,
        estimated_duration_minutes: Number(durationMinutes),
        skill_ids: selectedSkillIds,
      }
      const course = await creatorApi.createCourse(payload)
      onCreated(course)
      onClose()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to create new draft course.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950/60 rounded-xl text-indigo-400 border border-indigo-800/40">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Create New Course</h2>
              <p className="text-xs text-slate-400">Initialize a working draft to start authoring.</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form id="create-course-form" onSubmit={handleCreate} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-2 text-red-200 text-xs">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Course Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={handleTitleChange}
                placeholder="e.g. Distributed Systems in Python"
                className="w-full px-3.5 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                URL Identifier / Slug *
              </label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="distributed-systems-python"
                className="w-full px-3.5 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm font-mono"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Short Description (1-2 sentences) *
            </label>
            <textarea
              rows={2}
              value={shortDescription}
              onChange={(e) => setShortDescription(e.target.value)}
              placeholder="A high-impact course teaching consensus algorithms, state machines, and microservice resiliency."
              className="w-full px-3.5 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Discipline Category *
              </label>
              <select
                value={disciplineId}
                onChange={(e) => setDisciplineId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
                required
              >
                {disciplines.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Difficulty Level *
              </label>
              <select
                value={difficultyLevel}
                onChange={(e) => setDifficultyLevel(e.target.value as 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED')}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Duration (minutes) *
              </label>
              <input
                type="number"
                min={1}
                max={10000}
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Target Skills
            </label>
            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg">
              {skills.map((sk) => {
                const isSelected = selectedSkillIds.includes(sk.id)
                return (
                  <button
                    key={sk.id}
                    type="button"
                    onClick={() => handleToggleSkill(sk.id)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                      isSelected
                        ? 'bg-indigo-950/80 border-indigo-500 text-indigo-300'
                        : 'bg-slate-850 border-slate-750 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {sk.name}
                  </button>
                )
              })}
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/90">
          <Button type="button" variant="ghost" onClick={onClose} disabled={creating}>
            Cancel
          </Button>

          <Button
            type="submit"
            form="create-course-form"
            disabled={creating || loadingLookups}
            className="flex items-center gap-2 text-xs"
          >
            <Sparkles className="w-4 h-4" />
            {creating ? 'Initializing Course...' : 'Create Course Draft'}
          </Button>
        </div>
      </div>
    </div>
  )
}
