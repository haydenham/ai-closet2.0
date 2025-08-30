import { api } from './client'

export interface LoginRequest { email: string; password: string }
export interface LoginResponse { access_token: string; token_type: string }

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function login(req: LoginRequest): Promise<LoginResponse> {
  if (USE_MOCKS) {
    // Simulated network delay
    await new Promise(r => setTimeout(r, 50))
    return { access_token: 'mock-token', token_type: 'bearer' }
  }
  const res = await api.post<LoginResponse>('/auth/login', req)
  return res.data
}

export function storeToken(token: string) {
  localStorage.setItem('auth_token', token)
}

export function clearToken() { localStorage.removeItem('auth_token') }

export function getToken() { return localStorage.getItem('auth_token') }
