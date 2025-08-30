import { render, screen } from '@testing-library/react'
import App from './App'

test('renders site brand link', () => {
  render(<App />)
  const brand = screen.getByRole('link', { name: /Nomi/i })
  expect(brand).toBeInTheDocument()
})

test('renders welcome heading', () => {
  render(<App />)
  const headingElement = screen.getByRole('heading', { name: /Welcome/i, level: 1 })
  expect(headingElement).toBeInTheDocument()
})

test('navigates to feature extraction page', () => {
  window.history.pushState({}, '', '/features')
  render(<App />)
  expect(screen.getByRole('heading', { name: /Feature Extraction/i })).toBeInTheDocument()
})

test('navigates to login page', () => {
  window.history.pushState({}, '', '/login')
  render(<App />)
  expect(screen.getByRole('heading', { name: /Login/i })).toBeInTheDocument()
})