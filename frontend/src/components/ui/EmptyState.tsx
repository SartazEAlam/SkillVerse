import React from 'react'

export interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description: string
  action?: React.ReactNode
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-8 rounded-xl border border-dashed border-border-medium bg-bg-elevated/40 ${className}`}
    >
      {icon && (
        <div className="w-12 h-12 rounded-full bg-bg-surface flex items-center justify-center text-text-muted mb-4 border border-border-subtle">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-text-primary mb-1">{title}</h3>
      <p className="text-sm text-text-secondary max-w-sm mb-5">{description}</p>
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}
