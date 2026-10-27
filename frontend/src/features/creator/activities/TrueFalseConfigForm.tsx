import React from 'react'

interface TrueFalseConfigFormProps {
  config: {
    statement?: string
  }
  answerKey: {
    expected_answer?: boolean
    correct_boolean?: boolean
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const TrueFalseConfigForm: React.FC<TrueFalseConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const statement = config.statement || ''
  const expectedAnswer = answerKey.correct_boolean ?? answerKey.expected_answer ?? true

  const handleStatementChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...config, statement: e.target.value }, answerKey)
  }

  const handleAnswerChange = (val: boolean) => {
    onChange(config, { correct_boolean: val, expected_answer: val })
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Statement *
        </label>
        <input
          type="text"
          value={statement}
          onChange={handleStatementChange}
          placeholder="e.g. Python lists are mutable sequences."
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          required
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Correct Answer *
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label
            className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer font-medium text-sm transition-all ${
              expectedAnswer === true
                ? 'bg-emerald-950/40 border-emerald-500/60 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <input
              type="radio"
              name="tf-answer"
              checked={expectedAnswer === true}
              onChange={() => handleAnswerChange(true)}
              className="text-emerald-500 focus:ring-emerald-400"
            />
            True
          </label>

          <label
            className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer font-medium text-sm transition-all ${
              expectedAnswer === false
                ? 'bg-rose-950/40 border-rose-500/60 text-rose-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <input
              type="radio"
              name="tf-answer"
              checked={expectedAnswer === false}
              onChange={() => handleAnswerChange(false)}
              className="text-rose-500 focus:ring-rose-400"
            />
            False
          </label>
        </div>
      </div>
    </div>
  )
}
