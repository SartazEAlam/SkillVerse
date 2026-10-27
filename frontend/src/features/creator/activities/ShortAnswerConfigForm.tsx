import React from 'react'

interface ShortAnswerConfigFormProps {
  config: {
    question?: string
  }
  answerKey: {
    accepted_answers?: string[]
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

export const ShortAnswerConfigForm: React.FC<ShortAnswerConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const question = config.question || ''
  const acceptedAnswers = answerKey.accepted_answers || []
  const answersString = acceptedAnswers.join(', ')

  const handleQuestionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...config, question: e.target.value }, answerKey)
  }

  const handleAnswersChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const list = e.target.value
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
    onChange(config, { accepted_answers: list })
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
          placeholder="e.g. What is the Big-O time complexity of dictionary lookup in Python on average?"
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          required
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Accepted Answers (comma-separated) *
        </label>
        <input
          type="text"
          value={answersString}
          onChange={handleAnswersChange}
          placeholder="e.g. O(1), constant, O(1) constant time"
          className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-sm"
          required
        />
        <p className="text-xs text-slate-500 mt-1.5">
          Learner submissions will be normalized (trimmed, case-insensitive) and matched against this list.
        </p>
      </div>
    </div>
  )
}
