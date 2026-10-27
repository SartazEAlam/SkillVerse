import React from 'react'
import { Plus, Trash2, CheckCircle2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface Decision {
  id: string
  title: string
  description: string
}

interface ScenarioConfigFormProps {
  config: {
    narrative?: string
    decisions?: Decision[]
  }
  answerKey: {
    best_decision_id?: string
    acceptable_decision_ids?: string[]
  }
  feedbackConfig?: {
    explanations?: Record<string, string>
  }
  onChange: (
    config: Record<string, unknown>,
    answerKey: Record<string, unknown>,
    feedbackConfig?: Record<string, unknown>
  ) => void
}

export const ScenarioConfigForm: React.FC<ScenarioConfigFormProps> = ({
  config,
  answerKey,
  feedbackConfig,
  onChange,
}) => {
  const narrative = config.narrative || ''
  const decisions: Decision[] = config.decisions && config.decisions.length > 0
    ? config.decisions
    : [
        { id: 'dec-1', title: 'Option A: Quick Hotfix', description: 'Patch the live cluster directly.' },
        { id: 'dec-2', title: 'Option B: Staged Rollback', description: 'Revert release and investigate in staging.' },
      ]
  const bestId = answerKey.best_decision_id || decisions[0]?.id || ''
  const explanations = feedbackConfig?.explanations || {}

  const handleNarrativeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange({ ...config, narrative: e.target.value, decisions }, answerKey, feedbackConfig)
  }

  const handleDecisionFieldChange = (index: number, field: keyof Decision, val: string) => {
    const updated = [...decisions]
    updated[index] = { ...updated[index], [field]: val }
    onChange({ ...config, narrative, decisions: updated }, answerKey, feedbackConfig)
  }

  const handleExplanationChange = (id: string, text: string) => {
    const updatedExp = { ...explanations, [id]: text }
    onChange(
      { ...config, narrative, decisions },
      answerKey,
      { ...feedbackConfig, explanations: updatedExp }
    )
  }

  const handleSetBest = (id: string) => {
    onChange(
      { ...config, narrative, decisions },
      { ...answerKey, best_decision_id: id },
      feedbackConfig
    )
  }

  const addDecision = () => {
    const nextId = `dec-${Date.now()}`
    const updated = [...decisions, { id: nextId, title: '', description: '' }]
    onChange({ ...config, narrative, decisions: updated }, answerKey, feedbackConfig)
  }

  const removeDecision = (index: number) => {
    if (decisions.length <= 2) return
    const removedId = decisions[index].id
    const updated = decisions.filter((_, i) => i !== index)
    const nextBest = bestId === removedId ? updated[0]?.id : bestId
    onChange(
      { ...config, narrative, decisions: updated },
      { ...answerKey, best_decision_id: nextBest },
      feedbackConfig
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Scenario Narrative / Case Context *
        </label>
        <textarea
          rows={4}
          value={narrative}
          onChange={handleNarrativeChange}
          placeholder="e.g. During a peak traffic window, API latency spikes 500% due to an unindexed database query..."
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors text-sm"
          required
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Decision Options & Strategic Rationale *
          </label>
          <span className="text-xs text-slate-500">Click &quot;Optimal Choice&quot; to set the best action</span>
        </div>

        <div className="space-y-3">
          {decisions.map((d, idx) => (
            <div
              key={d.id}
              className={`p-3.5 rounded-lg border transition-all ${
                bestId === d.id
                  ? 'bg-indigo-950/40 border-indigo-500/60 ring-1 ring-indigo-500/30'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <button
                  type="button"
                  onClick={() => handleSetBest(d.id)}
                  className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md transition-colors ${
                    bestId === d.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {bestId === d.id ? 'Optimal Decision (100% Score)' : 'Set as Optimal'}
                </button>

                <button
                  type="button"
                  onClick={() => removeDecision(idx)}
                  disabled={decisions.length <= 2}
                  className="p-1 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                <input
                  type="text"
                  value={d.title}
                  onChange={(e) => handleDecisionFieldChange(idx, 'title', e.target.value)}
                  placeholder="Decision title (e.g. Option A: Rollback release)"
                  className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-medium"
                  required
                />
                <textarea
                  rows={2}
                  value={d.description}
                  onChange={(e) => handleDecisionFieldChange(idx, 'description', e.target.value)}
                  placeholder="Detailed description of the action and consequences..."
                  className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  required
                />
                <input
                  type="text"
                  value={explanations[d.id] || ''}
                  onChange={(e) => handleExplanationChange(d.id, e.target.value)}
                  placeholder="Learner feedback explanation when selecting this option"
                  className="w-full px-3 py-1.5 bg-slate-850 border border-slate-800 rounded text-xs text-slate-400 placeholder-slate-600 focus:outline-none focus:border-indigo-500 italic"
                />
              </div>
            </div>
          ))}
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addDecision}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Decision Option
        </Button>
      </div>
    </div>
  )
}
