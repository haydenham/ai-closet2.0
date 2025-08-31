import { api } from './client'

export interface LoginRequest { email: string; password: string }
export interface LoginResponse { access_token: string; token_type: string }

export interface RegisterRequest { 
  email: string; 
  password: string;
  first_name: string;
  last_name: string;
}

export interface RegisterResponse { 
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

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

export async function register(req: RegisterRequest): Promise<RegisterResponse> {
  if (USE_MOCKS) {
    // Simulated network delay
    await new Promise(r => setTimeout(r, 500))
    return { 
      id: 'mock-user-id',
      email: req.email,
      first_name: req.first_name,
      last_name: req.last_name,
      is_verified: false,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  }
  const res = await api.post<RegisterResponse>('/auth/register', req)
  return res.data
}

export function storeToken(token: string) {
  localStorage.setItem('auth_token', token)
}

export function clearToken() { localStorage.removeItem('auth_token') }

export function getToken() { return localStorage.getItem('auth_token') }
