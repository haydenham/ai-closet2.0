import { useState, useCallback } from 'react'
import { login, LoginRequest, storeToken, clearToken, getToken } from '../api/auth'

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => getToken())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const signIn = useCallback(async (credentials: LoginRequest) => {
    setError(null)
    setLoading(true)
    try {
      const res = await login(credentials)
      storeToken(res.access_token)
      setToken(res.access_token)
      return true
    } catch (e: any) {
      setError(e.message || 'Login failed')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const signOut = useCallback(() => {
    clearToken()
    setToken(null)
  }, [])

  return { token, authenticated: !!token, loading, error, signIn, signOut }
}
