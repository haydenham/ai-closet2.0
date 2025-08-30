import { render, screen } from '@testing-library/react'
import App from '../../App'

function resetAuth() {
  localStorage.removeItem('auth_token')
}

describe('Protected routes', () => {
  beforeEach(() => {
    resetAuth()
  })

  it('redirects to login when accessing /closet unauthenticated', () => {
    window.history.pushState({}, '', '/closet')
    render(<App />)
    expect(screen.getByRole('heading', { name: /Login/i })).toBeInTheDocument()
  })

  it('shows closet page when authenticated', () => {
    localStorage.setItem('auth_token', 'test-token')
    window.history.pushState({}, '', '/closet')
    render(<App />)
    expect(screen.getByRole('heading', { name: /Closet/i })).toBeInTheDocument()
  })
})
