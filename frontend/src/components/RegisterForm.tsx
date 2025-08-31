import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Alert } from '../components/ui/Alert'
import { useRegister } from '../hooks/useRegister'
import { RegisterRequest } from '../api/auth'

export function RegisterForm() {
  const navigate = useNavigate()
  const registerMutation = useRegister()
  
  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  })
  
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email'
    }

    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    } else if (!/[A-Z]/.test(formData.password)) {
      newErrors.password = 'Password must include an uppercase letter'
    } else if (!/[a-z]/.test(formData.password)) {
      newErrors.password = 'Password must include a lowercase letter'  
    } else if (!/[0-9]/.test(formData.password)) {
      newErrors.password = 'Password must include a number'
    } else if (['password', 'password1', 'password123', '12345678', 'qwerty', 'letmein'].includes(formData.password.toLowerCase())) {
      newErrors.password = 'Password is too common'
    }

    if (formData.password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    if (!formData.first_name) {
      newErrors.first_name = 'First name is required'
    } else if (!/^[A-Za-z .,'-]{1,50}$/.test(formData.first_name)) {
      newErrors.first_name = 'First name contains invalid characters'
    }

    if (!formData.last_name) {
      newErrors.last_name = 'Last name is required'
    } else if (!/^[A-Za-z .,'-]{1,50}$/.test(formData.last_name)) {
      newErrors.last_name = 'Last name contains invalid characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    registerMutation.mutate(formData, {
      onSuccess: () => {
        navigate('/login', { 
          state: { message: 'Account created successfully! Please log in.' }
        })
      }
    })
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold text-center mb-6">Create Account</h2>
        
        {registerMutation.error && (
          <Alert variant="error" className="mb-4">
            {registerMutation.error instanceof Error 
              ? registerMutation.error.message 
              : 'Registration failed. Please try again.'}
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Input
                type="text"
                name="first_name"
                placeholder="First Name"
                value={formData.first_name}
                onChange={handleChange}
                variant={errors.first_name ? 'error' : 'default'}
              />
              {errors.first_name && (
                <p className="text-red-500 text-sm mt-1">{errors.first_name}</p>
              )}
            </div>
            <div>
              <Input
                type="text"
                name="last_name"
                placeholder="Last Name"
                value={formData.last_name}
                onChange={handleChange}
                variant={errors.last_name ? 'error' : 'default'}
              />
              {errors.last_name && (
                <p className="text-red-500 text-sm mt-1">{errors.last_name}</p>
              )}
            </div>
          </div>

          <div>
            <Input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              variant={errors.email ? 'error' : 'default'}
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email}</p>
            )}
          </div>

          <div>
            <Input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              variant={errors.password ? 'error' : 'default'}
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password}</p>
            )}
          </div>

          <div>
            <Input
              type="password"
              name="confirmPassword"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                if (errors.confirmPassword) {
                  setErrors(prev => ({ ...prev, confirmPassword: '' }))
                }
              }}
              variant={errors.confirmPassword ? 'error' : 'default'}
            />
            {errors.confirmPassword && (
              <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
            )}
          </div>

          <Button 
            type="submit" 
            variant="primary" 
            className="w-full"
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 hover:text-blue-800 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
