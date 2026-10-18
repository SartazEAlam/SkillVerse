import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'base' | 'elevated' | 'surface' | 'inset'
  hoverEffect?: boolean
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  hoverEffect = false,
  className = '',
  ...props
}) => {
  const variantStyles = {
    base: 'bg-bg-base border border-border-subtle',
    elevated: 'bg-bg-elevated border border-border-subtle',
    surface: 'bg-bg-surface border border-border-subtle',
    inset: 'bg-bg-inset border border-border-subtle'
  }[variant]

  const hoverStyles = hoverEffect
    ? 'transition-all duration-200 hover:border-border-medium hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/30'
    : ''

  return (
    <div
      className={`rounded-xl p-5 ${variantStyles} ${hoverStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
