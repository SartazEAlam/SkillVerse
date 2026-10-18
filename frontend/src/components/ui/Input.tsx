import React from 'react'
import { X } from 'lucide-react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  hint?: string
  error?: string
  leftIcon?: React.ReactNode
  onClear?: () => void
}

export const Input: React.FC<InputProps> = ({
  label,
  hint,
  error,
  leftIcon,
  onClear,
  id,
  className = '',
  value,
  disabled,
  ...props
}) => {
  const generatedId = React.useId()
  const inputId = id || generatedId
  const hintId = `${inputId}-hint`
  const errorId = `${inputId}-error`

  const showClear = Boolean(onClear && value && String(value).length > 0 && !disabled)

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-text-secondary mb-1.5 uppercase tracking-wider"
        >
          {label}
        </label>
      )}

      <div className="relative flex items-center">
        {leftIcon && (
          <span className="absolute left-3.5 text-text-muted pointer-events-none flex items-center justify-center">
            {leftIcon}
          </span>
        )}

        <input
          id={inputId}
          value={value}
          disabled={disabled}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={`w-full bg-bg-inset border text-text-primary text-sm rounded-lg px-3.5 py-2.5 transition-all duration-150 placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-violet focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed ${
            leftIcon ? 'pl-10' : ''
          } ${showClear ? 'pr-10' : ''} ${
            error
              ? 'border-state-error focus:ring-state-error'
              : 'border-border-subtle hover:border-border-medium'
          } ${className}`}
          {...props}
        />

        {showClear && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Clear input"
            className="absolute right-3 p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {error && (
        <p id={errorId} className="mt-1.5 text-xs text-state-error font-medium" role="alert">
          {error}
        </p>
      )}

      {hint && !error && (
        <p id={hintId} className="mt-1.5 text-xs text-text-muted">
          {hint}
        </p>
      )}
    </div>
  )
}
