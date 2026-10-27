import React, { useState, useEffect } from 'react'
import { Save, Plus, Trash2, CheckCircle2, AlertCircle } from 'lucide-react'
import type { ApiCourseDetail } from '../../types/catalog'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface SkillOption {
  id: string
  name: string
  slug: string
}

interface CourseMetadataEditorProps {
  course: ApiCourseDetail
  availableSkills?: SkillOption[]
  onSaved: () => void
}

export const CourseMetadataEditor: React.FC<CourseMetadataEditorProps> = ({
  course,
  availableSkills = [],
  onSaved,
}) => {
  const [title, setTitle] = useState<string>(course.title)
  const [shortDescription, setShortDescription] = useState<string>(course.short_description || '')
  const [fullDescription, setFullDescription] = useState<string>(course.full_description || '')
  const [difficultyLevel, setDifficultyLevel] = useState<'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'>(
    (course.difficulty_level as 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED') || 'BEGINNER'
  )
  const [durationMinutes, setDurationMinutes] = useState<number>(course.estimated_duration_minutes || 60)
  const [objectives, setObjectives] = useState<string[]>(course.learning_objectives || [])
  const [newObjective, setNewObjective] = useState<string>('')
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>(
    course.skills?.map((s) => s.id) || []
  )

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setTitle(course.title)
    setShortDescription(course.short_description || '')
    setFullDescription(course.full_description || '')
    setDifficultyLevel((course.difficulty_level as 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED') || 'BEGINNER')
    setDurationMinutes(course.estimated_duration_minutes || 60)
    setObjectives(course.learning_objectives || [])
    setSelectedSkillIds(course.skills?.map((s) => s.id) || [])
    setHasUnsavedChanges(false)
  }, [course])

  const markChanged = () => {
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const handleAddObjective = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newObjective.trim()) return
    setObjectives((prev) => [...prev, newObjective.trim()])
    setNewObjective('')
    markChanged()
  }

  const handleRemoveObjective = (index: number) => {
    setObjectives((prev) => prev.filter((_, i) => i !== index))
    markChanged()
  }

  const handleToggleSkill = (skillId: string) => {
    setSelectedSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    )
    markChanged()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (title.trim().length < 3) {
      setError('Title must be at least 3 characters.')
      return
    }
    if (shortDescription.trim().length < 10) {
      setError('Short description must be at least 10 characters.')
      return
    }

    setSaving(true)
    setError(null)
    setSaveSuccess(false)

    try {
      await creatorApi.updateCourse(course.id, {
        title: title.trim(),
        short_description: shortDescription.trim(),
        full_description: fullDescription.trim() || undefined,
        difficulty_level: difficultyLevel,
        estimated_duration_minutes: Number(durationMinutes),
        learning_objectives: objectives,
        skill_ids: selectedSkillIds,
      })
      setHasUnsavedChanges(false)
      setSaveSuccess(true)
      onSaved()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to update course metadata.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            Course Metadata &amp; Objectives
            {hasUnsavedChanges && (
              <span className="text-[11px] font-semibold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded-full border border-amber-800/50">
                Unsaved changes
              </span>
            )}
            {saveSuccess && !hasUnsavedChanges && (
              <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/50 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Saved
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-400">
            Define course catalog identity, target skills, and expected outcomes.
          </p>
        </div>

        <Button
          type="submit"
          disabled={saving || !hasUnsavedChanges}
          className="flex items-center gap-2 text-xs"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Metadata'}
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-2 text-red-200 text-xs">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Course Title *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value)
              markChanged()
            }}
            placeholder="e.g. Scalable Python Systems & Architecture"
            className="w-full px-3.5 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm font-medium"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Difficulty Level *
            </label>
            <select
              value={difficultyLevel}
              onChange={(e) => {
                setDifficultyLevel(e.target.value as 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED')
                markChanged()
              }}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Estimated Duration (minutes) *
            </label>
            <input
              type="number"
              min={1}
              max={10000}
              value={durationMinutes}
              onChange={(e) => {
                setDurationMinutes(Number(e.target.value))
                markChanged()
              }}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Short Description (Catalog Preview) *
          </label>
          <textarea
            rows={2}
            value={shortDescription}
            onChange={(e) => {
              setShortDescription(e.target.value)
              markChanged()
            }}
            placeholder="Concise 1-2 sentence overview shown in search and catalog cards."
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Full Description / Syllabus Overview
          </label>
          <textarea
            rows={4}
            value={fullDescription}
            onChange={(e) => {
              setFullDescription(e.target.value)
              markChanged()
            }}
            placeholder="Detailed course description, prerequisites, and learning roadmap."
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
          />
        </div>
      </div>

      {/* Skills Association */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Associated Skill Badges ({selectedSkillIds.length})
        </label>
        <p className="text-xs text-slate-500">
          Learners who complete this course will build mastery evidence toward these skills.
        </p>

        <div className="flex flex-wrap gap-2 pt-1">
          {availableSkills.map((sk) => {
            const isSelected = selectedSkillIds.includes(sk.id)
            return (
              <button
                key={sk.id}
                type="button"
                onClick={() => handleToggleSkill(sk.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  isSelected
                    ? 'bg-indigo-950/60 border-indigo-500 text-indigo-300 ring-1 ring-indigo-500/40'
                    : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'
                }`}
              >
                {sk.name}
              </button>
            )
          })}
        </div>
      </div>

      {/* Learning Objectives */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Learning Objectives ({objectives.length})
        </label>

        <div className="space-y-2">
          {objectives.map((obj, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-2.5 bg-slate-800/60 border border-slate-750 rounded-lg text-xs text-slate-200"
            >
              <span>{obj}</span>
              <button
                type="button"
                onClick={() => handleRemoveObjective(idx)}
                className="p-1 text-slate-500 hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex gap-2 pt-2">
          <input
            type="text"
            value={newObjective}
            onChange={(e) => setNewObjective(e.target.value)}
            placeholder="e.g. Master asynchronous concurrency patterns in production"
            className="flex-1 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddObjective}
            className="text-xs shrink-0"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add Objective
          </Button>
        </div>
      </div>
    </form>
  )
}
