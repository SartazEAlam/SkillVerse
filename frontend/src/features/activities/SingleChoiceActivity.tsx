import React from 'react'
import type { OptionItem } from '../../types/activity'

interface SingleChoiceActivityProps {
  options: OptionItem[]
  selectedOptionId: string | null
  onChange: (optionId: string) => void
  disabled?: boolean
}

export const SingleChoiceActivity: React.FC<SingleChoiceActivityProps> = ({
  options = [],
  selectedOptionId,
  onChange,
  disabled = false,
}) => {
  return (
    <div
      role="radiogroup"
      aria-label="Select one option"
      className="space-y-2.5 my-4"
    >
      {options.map((option, index) => {
        const isSelected = selectedOptionId === option.id
        return (
          <label
            key={option.id}
            htmlFor={`option-${option.id}`}
            className={`flex items-start gap-3 p-3.5 sm:p-4 rounded-xl border transition-all cursor-pointer select-none ${
              isSelected
                ? 'bg-accent-violet/15 border-accent-violet text-text-primary shadow-[0_0_12px_rgba(139,92,246,0.2)]'
                : 'bg-bg-surface border-border-subtle hover:border-border-medium hover:bg-bg-elevated text-text-secondary'
            } ${disabled ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}`}
          >
            <input
              type="radio"
              id={`option-${option.id}`}
              name="single-choice-activity"
              value={option.id}
              checked={isSelected}
              disabled={disabled}
              onChange={() => onChange(option.id)}
              className="mt-0.5 h-4 w-4 text-accent-violet border-border-medium focus:ring-accent-violet shrink-0"
            />
            <div className="flex-1 text-sm sm:text-base leading-relaxed">
              <span className="font-mono text-xs font-semibold text-text-muted mr-2">
                {String.fromCharCode(65 + index)}.
              </span>
              <span>{option.text}</span>
            </div>
          </label>
        )
      })}
    </div>
  )
}
