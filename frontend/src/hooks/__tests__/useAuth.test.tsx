import { renderHook, act } from '@testing-library/react'
import { useAuth } from '../useAuth'

// Simple mock for localStorage in test environment
const store: Record<string, string> = {}
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: (k: string) => store[k] || null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] }
  }
})

vi.mock('../../api/auth', () => {
  return {
    login: async () => ({ access_token: 'token-123', token_type: 'bearer' }),
    storeToken: (t: string) => { store['auth_token'] = t },
    clearToken: () => { delete store['auth_token'] },
    getToken: () => store['auth_token'] || null
  }
})

describe('useAuth', () => {
  it('logs in and stores token', async () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.authenticated).toBe(false)
    await act(async () => {
      await result.current.signIn({ email: 'a@b.c', password: 'x' })
    })
    expect(result.current.authenticated).toBe(true)
    expect(result.current.token).toBe('token-123')
  })

  it('signOut clears token', async () => {
    const { result } = renderHook(() => useAuth())
    await act(async () => {
      await result.current.signIn({ email: 'a@b.c', password: 'x' })
    })
    act(() => { result.current.signOut() })
    expect(result.current.authenticated).toBe(false)
    expect(result.current.token).toBeNull()
  })
})
