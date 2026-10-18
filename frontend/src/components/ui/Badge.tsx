import React from 'react'

export type BadgeVariant = 'default' | 'violet' | 'cyan' | 'emerald' | 'amber' | 'outline'
export type BadgeSize = 'sm' | 'md'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  icon?: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  icon,
  className = '',
  ...props
}) => {
  const sizeStyles: Record<BadgeSize, string> = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5'
  }

  const variantStyles: Record<BadgeVariant, string> = {
    default:
      'bg-bg-surface text-text-secondary border border-border-subtle',
    violet:
      'bg-accent-violet/15 text-accent-violet border border-accent-violet/30',
    cyan:
      'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/30',
    emerald:
      'bg-state-success/15 text-state-success border border-state-success/30',
    amber:
      'bg-state-warning/15 text-state-warning border border-state-warning/30',
    outline:
      'bg-transparent text-text-muted border border-border-medium'
  }

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full uppercase tracking-wider select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  )
}
