import React, { useState } from 'react'
import { X, Eye, Code, AlertCircle, Save } from 'lucide-react'
import type { ActivityType } from '../../../types/activity'
import type { ActivityAuthoring, ActivityCreatePayload, ActivityUpdatePayload } from '../../../types/creator'
import { creatorApi } from '../../../services/creatorApi'
import { Button } from '../../../components/ui/Button'
import { SingleChoiceConfigForm } from './SingleChoiceConfigForm'
import { MultipleSelectConfigForm } from './MultipleSelectConfigForm'
import { TrueFalseConfigForm } from './TrueFalseConfigForm'
import { ShortAnswerConfigForm } from './ShortAnswerConfigForm'
import { FillBlankConfigForm } from './FillBlankConfigForm'
import { OrderingConfigForm } from './OrderingConfigForm'
import { MatchingConfigForm } from './MatchingConfigForm'
import { CodeExerciseConfigForm } from './CodeExerciseConfigForm'
import { ScenarioConfigForm } from './ScenarioConfigForm'
import { ActivityRenderer } from '../../activities/ActivityRenderer'

interface SkillOption {
  id: string
  name: string
  slug: string
}

interface ActivityEditorModalProps {
  lessonId: string
  courseSkills?: SkillOption[]
  activity?: ActivityAuthoring | null
  isOpen: boolean
  onClose: () => void
  onSaved: (activity: ActivityAuthoring) => void
}

const ACTIVITY_TYPES: Array<{ type: ActivityType; label: string; desc: string }> = [
  { type: 'single_choice', label: 'Single Choice Quiz', desc: 'Radio select one correct option' },
  { type: 'multiple_select', label: 'Multiple Select', desc: 'Checkbox select multiple correct options' },
  { type: 'true_false', label: 'True / False', desc: 'Binary statement validation' },
  { type: 'short_answer', label: 'Short Answer', desc: 'Exact match or keyword verification' },
  { type: 'fill_in_the_blank', label: 'Fill in the Blank', desc: 'Complete missing tokens in narrative' },
  { type: 'ordering', label: 'Sequencing / Ordering', desc: 'Arrange items in chronological or logical order' },
  { type: 'matching', label: 'Bipartite Matching', desc: 'Pair items between two columns' },
  { type: 'code_exercise', label: 'Coding Exercise', desc: 'Run code against isolated test suites' },
  { type: 'scenario', label: 'Strategic Scenario', desc: 'Case study with high-leverage decision branches' },
]

export const ActivityEditorModal: React.FC<ActivityEditorModalProps> = ({
  lessonId,
  courseSkills = [],
  activity,
  isOpen,
  onClose,
  onSaved,
}) => {
  const isEditing = Boolean(activity?.id)

  const [title, setTitle] = useState<string>(activity?.title || '')
  const [instructions, setInstructions] = useState<string>(
    activity?.instructions || 'Read the question and select the best answer.'
  )
  const [activityType, setActivityType] = useState<ActivityType>(
    activity?.activity_type || 'single_choice'
  )
  const [passingScore, setPassingScore] = useState<number>(activity?.passing_score ?? 70)
  const [maxAttempts, setMaxAttempts] = useState<number | undefined>(activity?.max_attempts ?? undefined)
  const [selectedSkillId, setSelectedSkillId] = useState<string>(activity?.skill_id || '')

  const [config, setConfig] = useState<Record<string, unknown>>(activity?.configuration || {})
  const [answerKey, setAnswerKey] = useState<Record<string, unknown>>(activity?.answer_key || {})
  const [feedbackConfig, setFeedbackConfig] = useState<Record<string, unknown> | undefined>(
    activity?.feedback_config || undefined
  )

  const [previewSubmissionState, setPreviewSubmissionState] = useState<Record<string, unknown>>({})
  const [isPreviewMode, setIsPreviewMode] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleConfigChange = (
    newConfig: Record<string, unknown>,
    newAnswerKey: Record<string, unknown>,
    newFeedbackConfig?: Record<string, unknown>
  ) => {
    setConfig(newConfig)
    setAnswerKey(newAnswerKey)
    if (newFeedbackConfig !== undefined) {
      setFeedbackConfig(newFeedbackConfig)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Activity title is required.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const chosenSkill = courseSkills.find((s) => s.id === selectedSkillId)
      const mergedConfig = {
        ...config,
        ...(chosenSkill
          ? { skill_id: chosenSkill.id, skill_slug: chosenSkill.slug }
          : {}),
      }

      let saved: ActivityAuthoring
      if (isEditing && activity) {
        const payload: ActivityUpdatePayload = {
          title: title.trim(),
          instructions,
          configuration: mergedConfig,
          skill_id: chosenSkill ? chosenSkill.id : '',
          skill_slug: chosenSkill ? chosenSkill.slug : '',
          passing_score: Number(passingScore),
          max_attempts: maxAttempts ? Number(maxAttempts) : undefined,
          answer_key: answerKey,
          feedback_config: feedbackConfig,
        }
        saved = await creatorApi.updateActivity(activity.id, payload)
      } else {
        const payload: ActivityCreatePayload = {
          lesson_id: lessonId,
          activity_type: activityType,
          title: title.trim(),
          instructions,
          configuration: mergedConfig,
          skill_id: chosenSkill?.id,
          skill_slug: chosenSkill?.slug,
          passing_score: Number(passingScore),
          max_attempts: maxAttempts ? Number(maxAttempts) : undefined,
          answer_key: answerKey,
          feedback_config: feedbackConfig,
        }
        saved = await creatorApi.createActivity(payload)
      }

      onSaved(saved)
      onClose()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to save activity configuration.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Code className="w-5 h-5 text-indigo-400" />
              {isEditing ? 'Edit Activity Configuration' : 'Create Interactive Activity'}
            </h2>
            <p className="text-xs text-slate-400">
              Configure parameters, instructions, grading rubric, and learner secrets.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsPreviewMode(!isPreviewMode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                isPreviewMode
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
              }`}
            >
              <Eye className="w-4 h-4" />
              {isPreviewMode ? 'Exit Live Preview' : 'Live Preview'}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-3 text-red-200 text-sm">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isPreviewMode ? (
            <div className="space-y-4">
              <div className="p-3 bg-amber-950/30 border border-amber-800/50 rounded-xl flex items-center gap-2 text-xs text-amber-300">
                <Eye className="w-4 h-4 text-amber-400" />
                <span>
                  Interactive Preview Mode: Test your activity just as learners will experience it.
                  Submissions in this preview do not affect scores or mastery records.
                </span>
              </div>

              <div className="p-6 bg-slate-950/60 rounded-xl border border-slate-800">
                <ActivityRenderer
                  activity={{
                    id: activity?.id || 'preview-act',
                    lesson_id: lessonId,
                    activity_type: activityType,
                    title: title || 'Activity Preview',
                    instructions: instructions || 'Complete the following task:',
                    configuration: config,
                    max_attempts: maxAttempts ?? null,
                    passing_score: passingScore,
                    sort_order: 0,
                    created_at: activity?.created_at || '2026-01-01T00:00:00Z',
                    updated_at: activity?.updated_at || '2026-01-01T00:00:00Z',
                  }}
                  submissionState={previewSubmissionState}
                  onSubmissionChange={(updated) =>
                    setPreviewSubmissionState((prev) => ({ ...prev, ...updated }))
                  }
                />
              </div>
            </div>
          ) : (
            <form id="activity-form" onSubmit={handleSave} className="space-y-6">
              {/* Type selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Activity Engine Type *
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  {ACTIVITY_TYPES.map((t) => (
                    <button
                      key={t.type}
                      type="button"
                      disabled={isEditing}
                      onClick={() => {
                        setActivityType(t.type)
                        setConfig({})
                        setAnswerKey({})
                      }}
                      className={`text-left p-3 rounded-xl border transition-all ${
                        activityType === t.type
                          ? 'bg-indigo-950/50 border-indigo-500 text-indigo-200 shadow-md ring-1 ring-indigo-500/40'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                      } ${isEditing ? 'opacity-80 cursor-not-allowed' : ''}`}
                    >
                      <div className="font-semibold text-xs text-slate-200">{t.label}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">{t.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title & Instructions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Activity Title *
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Async Await Comprehension Check"
                    className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Target Skill Association
                  </label>
                  <select
                    value={selectedSkillId}
                    onChange={(e) => setSelectedSkillId(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 text-sm"
                  >
                    <option value="">No skill attribution (general activity)</option>
                    {courseSkills.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.slug})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Learner Instructions / Guidance *
                </label>
                <textarea
                  rows={2}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="Provide guidance on what the learner should do and how this is evaluated."
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
                  required
                />
              </div>

              {/* Scoring & Limits */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-950/40 rounded-xl border border-slate-800/80">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Passing Score (0 - 100%)
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={passingScore}
                      onChange={(e) => setPassingScore(Number(e.target.value))}
                      className="flex-1 accent-indigo-500"
                    />
                    <span className="text-sm font-bold text-indigo-400 font-mono w-12 text-right">
                      {passingScore}%
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Maximum Allowed Attempts
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={maxAttempts ?? ''}
                    onChange={(e) =>
                      setMaxAttempts(e.target.value ? Number(e.target.value) : undefined)
                    }
                    placeholder="Unlimited attempts (default)"
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Dynamic Type Config Form */}
              <div className="p-5 bg-slate-950/60 rounded-xl border border-slate-800">
                <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-4 pb-2 border-b border-slate-800">
                  {activityType.replace(/_/g, ' ')} Configuration &amp; Answer Key
                </div>

                {activityType === 'single_choice' && (
                  <SingleChoiceConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'multiple_select' && (
                  <MultipleSelectConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'true_false' && (
                  <TrueFalseConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'short_answer' && (
                  <ShortAnswerConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'fill_in_the_blank' && (
                  <FillBlankConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'ordering' && (
                  <OrderingConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'matching' && (
                  <MatchingConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'code_exercise' && (
                  <CodeExerciseConfigForm
                    config={config}
                    answerKey={answerKey}
                    onChange={handleConfigChange}
                  />
                )}

                {activityType === 'scenario' && (
                  <ScenarioConfigForm
                    config={config}
                    answerKey={answerKey}
                    feedbackConfig={feedbackConfig}
                    onChange={handleConfigChange}
                  />
                )}
              </div>
            </form>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/90">
          <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>
            Cancel
          </Button>

          <Button
            type="submit"
            form="activity-form"
            disabled={saving}
            className="flex items-center gap-2"
          >
            {saving ? (
              'Saving...'
            ) : (
              <>
                <Save className="w-4 h-4" />
                {isEditing ? 'Save Changes' : 'Create Activity'}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
