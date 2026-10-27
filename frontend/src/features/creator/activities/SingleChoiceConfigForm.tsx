import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface Option {
  id: string
  text: string
}

interface SingleChoiceConfigFormProps {
  config: {
    question?: string
    options?: Option[]
  }
  answerKey: {
    selected_option_id?: string
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const SingleChoiceConfigForm: React.FC<SingleChoiceConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const question = config.question || ''
  const options: Option[] = config.options && config.options.length > 0
    ? config.options
    : [
        { id: 'opt-1', text: '' },
        { id: 'opt-2', text: '' },
      ]
  const selectedOptionId = answerKey.selected_option_id || options[0]?.id || ''

  const handleQuestionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...config, question: e.target.value, options }, answerKey)
  }

  const handleOptionTextChange = (id: string, text: string) => {
    const updated = options.map((opt) => (opt.id === id ? { ...opt, text } : opt))
    onChange({ ...config, question, options: updated }, answerKey)
  }

  const handleSelectCorrect = (id: string) => {
    onChange({ ...config, question, options }, { selected_option_id: id })
  }

  const addOption = () => {
    const nextId = `opt-${Date.now()}`
    const updated = [...options, { id: nextId, text: '' }]
    onChange({ ...config, question, options: updated }, answerKey)
  }

  const removeOption = (id: string) => {
    if (options.length <= 2) return
    const updated = options.filter((opt) => opt.id !== id)
    const nextAnswerKey =
      selectedOptionId === id ? { selected_option_id: updated[0]?.id } : answerKey
    onChange({ ...config, question, options: updated }, nextAnswerKey)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Question Prompt *
        </label>
        <input
          type="text"
          value={question}
          onChange={handleQuestionChange}
          placeholder="e.g. Which keyword declares an asynchronous function in Python?"
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          required
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Options & Correct Answer *
          </label>
          <span className="text-xs text-slate-500">Select the radio button for the correct answer</span>
        </div>

        <div className="space-y-2.5">
          {options.map((opt, idx) => (
            <div
              key={opt.id}
              className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all ${
                selectedOptionId === opt.id
                  ? 'bg-indigo-950/40 border-indigo-500/60'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <input
                type="radio"
                name="correct-option"
                id={`correct-${opt.id}`}
                checked={selectedOptionId === opt.id}
                onChange={() => handleSelectCorrect(opt.id)}
                className="w-4 h-4 text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500"
              />
              <span className="text-xs font-bold text-slate-400 w-5">
                {String.fromCharCode(65 + idx)}.
              </span>
              <input
                type="text"
                value={opt.text}
                onChange={(e) => handleOptionTextChange(opt.id, e.target.value)}
                placeholder={`Option ${String.fromCharCode(65 + idx)} text`}
                className="flex-1 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded-md text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />
              <button
                type="button"
                onClick={() => removeOption(opt.id)}
                disabled={options.length <= 2}
                className="p-1.5 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Remove option"
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
          onClick={addOption}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Option
        </Button>
      </div>
    </div>
  )
}
