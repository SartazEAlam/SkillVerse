import React from 'react'
import { Check, X } from 'lucide-react'

interface TrueFalseActivityProps {
  statement?: string
  selectedValue: boolean | null
  onChange: (value: boolean) => void
  disabled?: boolean
}

export const TrueFalseActivity: React.FC<TrueFalseActivityProps> = ({
  statement,
  selectedValue,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-4 my-4">
      {statement && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-medium text-sm sm:text-base text-text-primary leading-relaxed font-medium">
          &ldquo;{statement}&rdquo;
        </div>
      )}

      <div
        role="radiogroup"
        aria-label="True or False decision"
        className="grid grid-cols-1 sm:grid-cols-2 gap-3"
      >
        <button
          type="button"
          role="radio"
          aria-checked={selectedValue === true}
          disabled={disabled}
          onClick={() => onChange(true)}
          className={`flex items-center justify-center gap-3 p-4 rounded-xl border text-base font-semibold transition-all cursor-pointer select-none ${
            selectedValue === true
              ? 'bg-state-success/20 border-state-success text-state-success shadow-[0_0_16px_rgba(34,197,94,0.25)]'
              : 'bg-bg-surface border-border-subtle hover:border-border-medium text-text-secondary hover:text-text-primary'
          } ${disabled ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}`}
        >
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center ${
              selectedValue === true
                ? 'bg-state-success text-bg-base'
                : 'border border-border-medium text-text-muted'
            }`}
          >
            <Check className="w-4 h-4 stroke-[3]" />
          </div>
          <span>True</span>
        </button>

        <button
          type="button"
          role="radio"
          aria-checked={selectedValue === false}
          disabled={disabled}
          onClick={() => onChange(false)}
          className={`flex items-center justify-center gap-3 p-4 rounded-xl border text-base font-semibold transition-all cursor-pointer select-none ${
            selectedValue === false
              ? 'bg-state-error/20 border-state-error text-state-error shadow-[0_0_16px_rgba(239,68,68,0.25)]'
              : 'bg-bg-surface border-border-subtle hover:border-border-medium text-text-secondary hover:text-text-primary'
          } ${disabled ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}`}
        >
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center ${
              selectedValue === false
                ? 'bg-state-error text-bg-base'
                : 'border border-border-medium text-text-muted'
            }`}
          >
            <X className="w-4 h-4 stroke-[3]" />
          </div>
          <span>False</span>
        </button>
      </div>
    </div>
  )
}
