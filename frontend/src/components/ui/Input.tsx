import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../utils/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'error'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const baseClasses = 'w-full border rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 transition-colors'
    
    const variants = {
      default: 'border-neutral-300 focus:ring-neutral-500 focus:border-neutral-500',
      error: 'border-red-300 focus:ring-red-500 focus:border-red-500'
    }
    
    return (
      <input
        ref={ref}
        className={cn(baseClasses, variants[variant], className)}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
