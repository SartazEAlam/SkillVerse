import React from 'react'

export interface ProgressBarProps {
  value: number // 0 to 100
  label?: string
  showPercentage?: boolean
  variant?: 'violet' | 'cyan' | 'emerald'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercentage = false,
  variant = 'violet',
  size = 'md',
  className = ''
}) => {
  const clampedValue = Math.min(100, Math.max(0, Math.round(value)))

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-3.5'
  }[size]

  const variantStyles = {
    violet: 'bg-accent-violet shadow-[0_0_8px_rgba(139,92,246,0.5)]',
    cyan: 'bg-accent-cyan shadow-[0_0_8px_rgba(6,182,212,0.5)]',
    emerald: 'bg-state-success shadow-[0_0_8px_rgba(16,185,129,0.5)]'
  }[variant]

  return (
    <div className={`w-full ${className}`}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-xs mb-1.5">
          {label && <span className="font-medium text-text-secondary">{label}</span>}
          {showPercentage && <span className="font-mono text-text-muted">{clampedValue}%</span>}
        </div>
      )}

      <div
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || 'Progress'}
        className={`w-full bg-bg-inset border border-border-subtle rounded-full overflow-hidden ${heightStyles}`}
      >
        <div
          className={`h-full transition-all duration-300 ease-out rounded-full ${variantStyles}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  )
}
