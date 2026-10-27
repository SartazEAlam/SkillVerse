import React from 'react'
import { Plus, Trash2, ArrowRight } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface Pair {
  id: string
  leftText: string
  rightText: string
}

interface MatchingConfigFormProps {
  config: {
    prompt?: string
    left_items?: Array<{ id: string; text: string }>
    right_items?: Array<{ id: string; text: string }>
  }
  answerKey: {
    pairs?: Record<string, string>
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const MatchingConfigForm: React.FC<MatchingConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const prompt = config.prompt || ''

  // Reconstruct pairs from left_items and answerKey.pairs
  const pairs: Pair[] = React.useMemo(() => {
    if (config.left_items && config.left_items.length > 0) {
      const rightMap = new Map((config.right_items || []).map((r) => [r.id, r.text]))
      const keyPairs = answerKey.pairs || {}
      return config.left_items.map((l, idx) => {
        const rightId = keyPairs[l.id] || `r-${idx + 1}`
        return {
          id: l.id,
          leftText: l.text,
          rightText: rightMap.get(rightId) || '',
        }
      })
    }
    return [
      { id: 'l-1', leftText: 'FastAPI', rightText: 'Python Async Web Framework' },
      { id: 'l-2', leftText: 'Alembic', rightText: 'Database Migration Engine' },
    ]
  }, [config.left_items, config.right_items, answerKey.pairs])

  const serializeAndChange = (updatedPairs: Pair[], newPrompt: string = prompt) => {
    const left_items = updatedPairs.map((p) => ({ id: p.id, text: p.leftText }))
    const right_items = updatedPairs.map((p, idx) => ({ id: `r-${idx + 1}`, text: p.rightText }))
    const keyPairs: Record<string, string> = {}
    updatedPairs.forEach((p, idx) => {
      keyPairs[p.id] = `r-${idx + 1}`
    })

    onChange(
      {
        ...config,
        prompt: newPrompt,
        left_items,
        right_items,
      },
      { pairs: keyPairs }
    )
  }

  const handlePromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    serializeAndChange(pairs, e.target.value)
  }

  const handleLeftChange = (index: number, text: string) => {
    const updated = [...pairs]
    updated[index] = { ...updated[index], leftText: text }
    serializeAndChange(updated)
  }

  const handleRightChange = (index: number, text: string) => {
    const updated = [...pairs]
    updated[index] = { ...updated[index], rightText: text }
    serializeAndChange(updated)
  }

  const addPair = () => {
    const nextId = `l-${Date.now()}`
    const updated = [...pairs, { id: nextId, leftText: '', rightText: '' }]
    serializeAndChange(updated)
  }

  const removePair = (index: number) => {
    if (pairs.length <= 2) return
    const updated = pairs.filter((_, i) => i !== index)
    serializeAndChange(updated)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Matching Instructions / Prompt *
        </label>
        <input
          type="text"
          value={prompt}
          onChange={handlePromptChange}
          placeholder="e.g. Match each component to its primary architecture responsibility."
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          required
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Matching Pairs *
          </label>
          <span className="text-xs text-slate-500">Each left item matches the corresponding right item</span>
        </div>

        <div className="space-y-2.5">
          {pairs.map((p, idx) => (
            <div
              key={p.id}
              className="flex items-center gap-2 p-2.5 bg-slate-900/60 border border-slate-800 rounded-lg"
            >
              <input
                type="text"
                value={p.leftText}
                onChange={(e) => handleLeftChange(idx, e.target.value)}
                placeholder="Left item"
                className="flex-1 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />

              <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

              <input
                type="text"
                value={p.rightText}
                onChange={(e) => handleRightChange(idx, e.target.value)}
                placeholder="Right matching item"
                className="flex-1 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />

              <button
                type="button"
                onClick={() => removePair(idx)}
                disabled={pairs.length <= 2}
                className="p-1.5 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Remove pair"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addPair}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Pair
        </Button>
      </div>
    </div>
  )
}
