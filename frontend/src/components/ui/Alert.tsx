import React from 'react'
import { cn } from '../../utils/cn'

interface AlertProps {
  children: React.ReactNode
  variant?: 'error' | 'warning' | 'info' | 'success'
  className?: string
}

export const Alert: React.FC<AlertProps> = ({ 
  children, 
  variant = 'info', 
  className 
}) => {
  const variantClasses = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800'
  }

  return (
    <div 
      className={cn(
        'border rounded-sm px-4 py-3 text-sm',
        variantClasses[variant],
        className
      )}
      role="alert"
    >
      {children}
    </div>
  )
}

interface ErrorMessageProps {
  error?: string | null
  fallback?: string
  className?: string
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  error, 
  fallback = 'An error occurred',
  className 
}) => {
  if (!error) return null
  
  return (
    <Alert variant="error" className={className}>
      {error || fallback}
    </Alert>
  )
}
