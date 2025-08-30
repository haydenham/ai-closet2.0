import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { signIn, loading, error } = useAuth()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email || !password) return
    const ok = await signIn({ email, password })
    if (ok) {
      // naive redirect
      window.location.href = '/'
    }
  }

  return (
    <div className="max-w-sm">
      <h1 className="text-xl font-semibold tracking-tight mb-6">Login</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
            placeholder="you@example.com"
            autoComplete="email"
          />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium">Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </div>
  {error && <div className="text-sm text-red-600">{error}</div>}
        <button
          type="submit"
            disabled={loading}
          className="h-9 px-4 rounded-sm bg-neutral-900 text-white text-sm font-medium tracking-tight disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-800 transition-colors w-full"
        >
          {loading ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
