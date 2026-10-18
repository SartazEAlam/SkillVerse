import React from 'react'
import type { ButtonSize, ButtonVariant } from './Button'

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  'aria-label': string
  icon: React.ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  'aria-label': ariaLabel,
  variant = 'ghost',
  size = 'md',
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center transition-all duration-150 rounded-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base'

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg'
  }

  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      'bg-accent-violet text-white hover:bg-accent-violet-hover active:scale-95 shadow-sm',
    secondary:
      'bg-bg-surface text-text-primary border border-border-subtle hover:border-border-medium hover:bg-bg-elevated active:scale-95',
    outline:
      'border border-border-medium text-text-primary hover:bg-bg-surface hover:border-accent-violet active:scale-95',
    ghost:
      'text-text-secondary hover:text-text-primary hover:bg-bg-surface active:scale-95',
    destructive:
      'bg-state-error text-white hover:opacity-90 active:scale-95'
  }

  return (
    <button
      aria-label={ariaLabel}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon}
    </button>
  )
}
