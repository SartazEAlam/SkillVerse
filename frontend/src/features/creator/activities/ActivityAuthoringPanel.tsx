import React, { useState } from 'react'
import { Plus, Edit, Trash2, Award, Zap, AlertCircle } from 'lucide-react'
import type { ActivityAuthoring } from '../../../types/creator'
import { creatorApi } from '../../../services/creatorApi'
import { Button } from '../../../components/ui/Button'
import { ActivityEditorModal } from './ActivityEditorModal'

interface SkillOption {
  id: string
  name: string
  slug: string
}

interface ActivityAuthoringPanelProps {
  lessonId: string
  lessonTitle: string
  activities: ActivityAuthoring[]
  courseSkills?: SkillOption[]
  onActivitiesChanged: () => void
}

export const ActivityAuthoringPanel: React.FC<ActivityAuthoringPanelProps> = ({
  lessonId,
  lessonTitle,
  activities,
  courseSkills = [],
  onActivitiesChanged,
}) => {
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const [editingActivity, setEditingActivity] = useState<ActivityAuthoring | null>(null)
  const [loadingEditId, setLoadingEditId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleOpenCreate = () => {
    setEditingActivity(null)
    setModalOpen(true)
  }

  const handleOpenEdit = async (act: ActivityAuthoring) => {
    setLoadingEditId(act.id)
    setError(null)
    try {
      const full = await creatorApi.getAuthoringActivity(act.id)
      setEditingActivity(full)
      setModalOpen(true)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to fetch activity authoring secrets.')
    } finally {
      setLoadingEditId(null)
    }
  }

  const handleDelete = async (activityId: string, title: string) => {
    if (!window.confirm(`Are you sure you want to delete the activity "${title}"?`)) {
      return
    }

    setDeletingId(activityId)
    setError(null)
    try {
      await creatorApi.deleteActivity(activityId)
      onActivitiesChanged()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to delete activity.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-200">
            Assessments &amp; Activities ({activities.length})
          </h3>
          <p className="text-xs text-slate-400">
            Interactive checks that award learner mastery points for &quot;{lessonTitle}&quot;.
          </p>
        </div>

        <Button
          type="button"
          size="sm"
          onClick={handleOpenCreate}
          className="flex items-center gap-1.5 text-xs"
        >
          <Plus className="w-4 h-4" />
          Add Activity
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-2 text-red-200 text-xs">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {activities.length === 0 ? (
        <div className="p-8 text-center bg-slate-900/40 border border-slate-800 border-dashed rounded-xl">
          <Zap className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-300">No activities configured yet</p>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            Interactive activities provide immediate feedback and generate verifiable skill mastery evidence.
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleOpenCreate}
            className="text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add First Activity
          </Button>
        </div>
      ) : (
        <div className="space-y-2.5">
          {activities.map((act) => {
            const skillName = courseSkills.find((s) => s.id === act.skill_id)?.name
            return (
              <div
                key={act.id}
                className="flex items-center justify-between p-3.5 bg-slate-900/70 border border-slate-800 hover:border-slate-700 rounded-xl transition-all"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/40 text-indigo-400">
                      {act.activity_type.replace(/_/g, ' ')}
                    </span>
                    <h4 className="text-sm font-semibold text-slate-100">{act.title}</h4>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Award className="w-3.5 h-3.5 text-amber-400" />
                      Pass: {act.passing_score ?? 70}%
                    </span>

                    {skillName && (
                      <span className="text-xs text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                        Assesses: {skillName}
                      </span>
                    )}

                    {act.max_attempts && (
                      <span className="text-slate-500">
                        Max attempts: {act.max_attempts}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => handleOpenEdit(act)}
                    disabled={loadingEditId === act.id}
                    className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Edit activity"
                  >
                    <Edit className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDelete(act.id, act.title)}
                    disabled={deletingId === act.id}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Delete activity"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modalOpen && (
        <ActivityEditorModal
          lessonId={lessonId}
          courseSkills={courseSkills}
          activity={editingActivity}
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onSaved={() => {
            onActivitiesChanged()
          }}
        />
      )}
    </div>
  )
}
