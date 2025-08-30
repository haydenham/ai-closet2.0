import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../utils/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center rounded-sm font-medium tracking-tight transition-colors focus:outline-none focus:ring-1 focus:ring-neutral-500 disabled:opacity-40 disabled:cursor-not-allowed'
    
    const variants = {
      primary: 'bg-neutral-900 text-white hover:bg-neutral-800',
      secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200',
      outline: 'border border-neutral-300 bg-white text-neutral-900 hover:bg-neutral-50'
    }
    
    const sizes = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-9 px-4 text-sm',
      lg: 'h-10 px-6 text-sm'
    }
    
    return (
      <button
        ref={ref}
        className={cn(baseClasses, variants[variant], sizes[size], className)}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
