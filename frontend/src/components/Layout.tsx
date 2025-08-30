import { PropsWithChildren } from 'react'
import { Link } from 'react-router-dom'

export function Layout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-neutral-900">
      <header className="border-b border-neutral-200">
        <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold tracking-tight">AI Closet</Link>
          <nav className="flex items-center gap-6 text-sm">
            <Link to="/features" className="hover:text-neutral-600 transition-colors">Features</Link>
            <Link to="/recommendations" className="hover:text-neutral-600 transition-colors">Recommendations</Link>
            <Link to="/closet" className="hover:text-neutral-600 transition-colors">Closet</Link>
            {localStorage.getItem('auth_token') ? (
              <button
                onClick={() => {
                  localStorage.removeItem('auth_token')
                  window.location.href = '/login'
                }}
                className="text-xs font-medium px-3 py-1.5 border border-neutral-300 rounded-sm hover:bg-neutral-50 transition-colors"
              >Logout</button>
            ) : (
              <Link to="/login" className="hover:text-neutral-600 transition-colors">Login</Link>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
