import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface BlankItem {
  id: string
  hint?: string
}

interface FillBlankConfigFormProps {
  config: {
    template?: string
    blanks?: BlankItem[]
  }
  answerKey: {
    blanks?: Record<string, { accepted_answers: string[]; case_sensitive?: boolean }>
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const FillBlankConfigForm: React.FC<FillBlankConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const template = config.template || ''
  const blanks: BlankItem[] = config.blanks && config.blanks.length > 0
    ? config.blanks
    : [{ id: 'blank_1', hint: 'keyword' }]
  const keyBlanks = answerKey.blanks || { blank_1: { accepted_answers: ['async'] } }

  const handleTemplateChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange({ ...config, template: e.target.value, blanks }, answerKey)
  }

  const handleBlankHintChange = (id: string, hint: string) => {
    const updated = blanks.map((b) => (b.id === id ? { ...b, hint } : b))
    onChange({ ...config, template, blanks: updated }, answerKey)
  }

  const handleBlankAnswersChange = (id: string, answersText: string) => {
    const answersList = answersText
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
    const updatedKeyBlanks = {
      ...keyBlanks,
      [id]: {
        ...(keyBlanks[id] || {}),
        accepted_answers: answersList,
      },
    }
    onChange(config, { blanks: updatedKeyBlanks })
  }

  const addBlank = () => {
    const nextId = `blank_${blanks.length + 1}`
    const updated = [...blanks, { id: nextId, hint: '' }]
    const updatedKeyBlanks = {
      ...keyBlanks,
      [nextId]: { accepted_answers: [''] },
    }
    onChange({ ...config, template, blanks: updated }, { blanks: updatedKeyBlanks })
  }

  const removeBlank = (id: string) => {
    if (blanks.length <= 1) return
    const updated = blanks.filter((b) => b.id !== id)
    const updatedKeyBlanks = { ...keyBlanks }
    delete updatedKeyBlanks[id]
    onChange({ ...config, template, blanks: updated }, { blanks: updatedKeyBlanks })
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Template Text (use {`{{blank_id}}`} for inputs) *
        </label>
        <textarea
          rows={3}
          value={template}
          onChange={handleTemplateChange}
          placeholder="e.g. To declare an asynchronous function in Python, use the {{blank_1}} keyword before def."
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-sm"
          required
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Configured Blanks & Expected Answers *
        </label>

        <div className="space-y-3">
          {blanks.map((b) => {
            const currentAnswers = keyBlanks[b.id]?.accepted_answers || []
            return (
              <div
                key={b.id}
                className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg space-y-2.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                    {`{{${b.id}}}`}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeBlank(b.id)}
                    disabled={blanks.length <= 1}
                    className="p-1 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Accepted Answers (comma-separated)</label>
                    <input
                      type="text"
                      value={currentAnswers.join(', ')}
                      onChange={(e) => handleBlankAnswersChange(b.id, e.target.value)}
                      placeholder="e.g. async, Async"
                      className="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Optional Hint</label>
                    <input
                      type="text"
                      value={b.hint || ''}
                      onChange={(e) => handleBlankHintChange(b.id, e.target.value)}
                      placeholder="e.g. 5-letter keyword"
                      className="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addBlank}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Blank
        </Button>
      </div>
    </div>
  )
}
