import { useMutation } from '@tanstack/react-query'
import { register } from '../api/auth'

export function useRegister() {
  return useMutation({
    mutationFn: register,
    onSuccess: (data) => {
      console.log('Registration successful:', data)
    },
    onError: (error) => {
      console.error('Registration failed:', error)
    }
  })
}
