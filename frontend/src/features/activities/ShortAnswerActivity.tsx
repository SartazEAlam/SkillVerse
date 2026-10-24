import React from 'react'

interface ShortAnswerActivityProps {
  prompt?: string
  placeholder?: string
  maxLength?: number
  value: string
  onChange: (val: string) => void
  disabled?: boolean
}

export const ShortAnswerActivity: React.FC<ShortAnswerActivityProps> = ({
  prompt,
  placeholder = 'Type your concise answer here...',
  maxLength = 1000,
  value = '',
  onChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-3 my-4">
      {prompt && (
        <label
          htmlFor="short-answer-input"
          className="block text-sm font-medium text-text-primary leading-relaxed"
        >
          {prompt}
        </label>
      )}

      <div className="relative">
        <textarea
          id="short-answer-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          maxLength={maxLength}
          disabled={disabled}
          placeholder={placeholder}
          rows={3}
          className="w-full p-3.5 rounded-xl bg-bg-surface border border-border-medium text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet transition-all text-sm leading-relaxed resize-y disabled:opacity-70 disabled:cursor-not-allowed font-sans"
        />
        <div className="flex justify-end pt-1 text-xs font-mono text-text-muted">
          <span>
            {value.length} / {maxLength} chars
          </span>
        </div>
      </div>
    </div>
  )
}
