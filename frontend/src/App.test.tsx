import { render, screen } from '@testing-library/react'
import App from './App'

test('renders Fashion AI Platform heading', () => {
  render(<App />)
  const headingElement = screen.getByRole('heading', { name: /Fashion AI Platform/i, level: 1 })
  expect(headingElement).toBeInTheDocument()
})

test('renders welcome message', () => {
  render(<App />)
  const welcomeElement = screen.getByText(/Welcome to Fashion AI Platform/i)
  expect(welcomeElement).toBeInTheDocument()
})