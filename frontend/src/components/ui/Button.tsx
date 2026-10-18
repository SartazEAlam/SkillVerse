import React from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'destructive'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-150 rounded-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base'

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 h-8',
    md: 'text-sm px-4 py-2 gap-2 h-10',
    lg: 'text-base px-5 py-2.5 gap-2.5 h-12'
  }

  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      'bg-accent-violet text-white hover:bg-accent-violet-hover active:scale-[0.98] shadow-sm hover:shadow-[0_0_16px_rgba(139,92,246,0.35)]',
    secondary:
      'bg-bg-surface text-text-primary border border-border-subtle hover:border-border-medium hover:bg-bg-elevated active:scale-[0.98]',
    outline:
      'border border-border-medium text-text-primary hover:bg-bg-surface hover:border-accent-violet active:scale-[0.98]',
    ghost:
      'text-text-secondary hover:text-text-primary hover:bg-bg-surface active:scale-[0.98]',
    destructive:
      'bg-state-error text-white hover:opacity-90 active:scale-[0.98]'
  }

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span
          className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"
          role="status"
          aria-label="Loading"
        />
      ) : (
        <>
          {leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
          <span>{children}</span>
          {rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
        </>
      )}
    </button>
  )
}
