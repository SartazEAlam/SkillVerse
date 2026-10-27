import React from 'react'
import { ArrowUp, ArrowDown, Plus, Trash2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface OrderItem {
  id: string
  text: string
}

interface OrderingConfigFormProps {
  config: {
    prompt?: string
    items?: OrderItem[]
  }
  answerKey: {
    correct_order?: string[]
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const OrderingConfigForm: React.FC<OrderingConfigFormProps> = ({
  config,
  answerKey: _answerKey,
  onChange,
}) => {
  const prompt = config.prompt || ''
  const items: OrderItem[] = config.items && config.items.length > 0
    ? config.items
    : [
        { id: 'it-1', text: 'Step 1: Define schema' },
        { id: 'it-2', text: 'Step 2: Generate migration' },
        { id: 'it-3', text: 'Step 3: Apply migration' },
      ]

  const handlePromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...config, prompt: e.target.value, items }, { correct_order: items.map((i) => i.id) })
  }

  const handleItemTextChange = (id: string, text: string) => {
    const updated = items.map((it) => (it.id === id ? { ...it, text } : it))
    onChange({ ...config, prompt, items: updated }, { correct_order: updated.map((i) => i.id) })
  }

  const moveItem = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= items.length) return

    const updated = [...items]
    const [moved] = updated.splice(index, 1)
    updated.splice(targetIndex, 0, moved)

    onChange({ ...config, prompt, items: updated }, { correct_order: updated.map((i) => i.id) })
  }

  const addItem = () => {
    const nextId = `it-${Date.now()}`
    const updated = [...items, { id: nextId, text: '' }]
    onChange({ ...config, prompt, items: updated }, { correct_order: updated.map((i) => i.id) })
  }

  const removeItem = (id: string) => {
    if (items.length <= 2) return
    const updated = items.filter((it) => it.id !== id)
    onChange({ ...config, prompt, items: updated }, { correct_order: updated.map((i) => i.id) })
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Ordering Instructions / Prompt *
        </label>
        <input
          type="text"
          value={prompt}
          onChange={handlePromptChange}
          placeholder="e.g. Arrange the steps of the database migration lifecycle in chronological order."
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          required
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Items in Correct Sequence *
          </label>
          <span className="text-xs text-slate-500">
            Arrange in the target correct order. The learner will see them shuffled.
          </span>
        </div>

        <div className="space-y-2">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className="flex items-center gap-2 p-2 bg-slate-900/60 border border-slate-800 rounded-lg"
            >
              <div className="flex flex-col">
                <button
                  type="button"
                  onClick={() => moveItem(idx, 'up')}
                  disabled={idx === 0}
                  className="p-0.5 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                >
                  <ArrowUp className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => moveItem(idx, 'down')}
                  disabled={idx === items.length - 1}
                  className="p-0.5 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                >
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
              </div>

              <span className="text-xs font-mono font-bold text-slate-500 w-6 text-center">
                #{idx + 1}
              </span>

              <input
                type="text"
                value={item.text}
                onChange={(e) => handleItemTextChange(item.id, e.target.value)}
                placeholder={`Step ${idx + 1}`}
                className="flex-1 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />

              <button
                type="button"
                onClick={() => removeItem(item.id)}
                disabled={items.length <= 2}
                className="p-1.5 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Remove item"
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
          onClick={addItem}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Item
        </Button>
      </div>
    </div>
  )
}

