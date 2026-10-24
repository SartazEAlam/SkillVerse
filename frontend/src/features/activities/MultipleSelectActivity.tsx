import React from 'react'
import type { OptionItem } from '../../types/activity'

interface MultipleSelectActivityProps {
  options: OptionItem[]
  selectedOptionIds: string[]
  onChange: (optionIds: string[]) => void
  disabled?: boolean
}

export const MultipleSelectActivity: React.FC<MultipleSelectActivityProps> = ({
  options = [],
  selectedOptionIds = [],
  onChange,
  disabled = false,
}) => {
  const handleToggle = (id: string) => {
    if (disabled) return
    if (selectedOptionIds.includes(id)) {
      onChange(selectedOptionIds.filter((item) => item !== id))
    } else {
      onChange([...selectedOptionIds, id])
    }
  }

  return (
    <div className="space-y-3 my-4">
      <div className="text-xs font-mono uppercase tracking-wider text-accent-cyan flex items-center gap-1.5">
        <span>Select all correct options:</span>
      </div>

      <div role="group" aria-label="Multiple options" className="space-y-2.5">
        {options.map((option, index) => {
          const isSelected = selectedOptionIds.includes(option.id)
          return (
            <label
              key={option.id}
              htmlFor={`multi-${option.id}`}
              className={`flex items-start gap-3 p-3.5 sm:p-4 rounded-xl border transition-all cursor-pointer select-none ${
                isSelected
                  ? 'bg-accent-cyan/15 border-accent-cyan text-text-primary shadow-[0_0_12px_rgba(6,182,212,0.2)]'
                  : 'bg-bg-surface border-border-subtle hover:border-border-medium hover:bg-bg-elevated text-text-secondary'
              } ${disabled ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}`}
            >
              <input
                type="checkbox"
                id={`multi-${option.id}`}
                value={option.id}
                checked={isSelected}
                disabled={disabled}
                onChange={() => handleToggle(option.id)}
                className="mt-0.5 h-4 w-4 rounded text-accent-cyan border-border-medium focus:ring-accent-cyan shrink-0"
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
    </div>
  )
}
