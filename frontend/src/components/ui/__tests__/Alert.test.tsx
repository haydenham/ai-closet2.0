import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Alert, ErrorMessage } from '../Alert'

describe('Alert Component', () => {
  it('renders with default variant', () => {
    render(<Alert>Test message</Alert>)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Test message')
    expect(alert).toHaveClass('bg-blue-50', 'border-blue-200', 'text-blue-800')
  })

  it('renders with error variant', () => {
    render(<Alert variant="error">Error message</Alert>)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800')
  })

  it('renders with success variant', () => {
    render(<Alert variant="success">Success message</Alert>)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('bg-green-50', 'border-green-200', 'text-green-800')
  })

  it('renders with warning variant', () => {
    render(<Alert variant="warning">Warning message</Alert>)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('bg-yellow-50', 'border-yellow-200', 'text-yellow-800')
  })

  it('applies custom className', () => {
    render(<Alert className="custom-class">Test</Alert>)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('custom-class')
  })
})

describe('ErrorMessage Component', () => {
  it('renders error message when error is provided', () => {
    render(<ErrorMessage error="Something went wrong" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Something went wrong')
    expect(alert).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800')
  })

  it('renders fallback message when error is provided', () => {
    render(<ErrorMessage error="Custom error" fallback="Default error" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Custom error')
  })

  it('renders fallback when error is empty string', () => {
    render(<ErrorMessage error="" fallback="Default error" />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render when no error', () => {
    render(<ErrorMessage error={null} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<ErrorMessage error="Test error" className="custom-error" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('custom-error')
  })
})
