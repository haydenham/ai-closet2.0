import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { getToken } from '../api/auth'

interface Props { children: ReactNode }

export function ProtectedRoute({ children }: Props) {
  const token = getToken()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}
