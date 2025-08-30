import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    // Optionally route to login
    localStorage.removeItem('auth_token')
  }
  return Promise.reject(err)
})

export interface Paginated<T> { items: T[]; total: number }
