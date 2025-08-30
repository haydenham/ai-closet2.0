import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Button, Input } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'

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
      <form onSubmit={onSubmit} className={layoutClasses.form}>
        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium">Email</label>
          <Input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            variant={error ? 'error' : 'default'}
          />
        </div>
        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium">Password</label>
          <Input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            variant={error ? 'error' : 'default'}
          />
        </div>
        <ErrorMessage error={error} />
        <Button
          type="submit"
          disabled={loading}
          className="w-full"
        >
          {loading ? 'Signing in…' : 'Sign In'}
        </Button>
      </form>
    </div>
  )
}