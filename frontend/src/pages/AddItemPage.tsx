import React from 'react'
import { useNavigate } from 'react-router-dom'
import { AddItemForm } from '../components/AddItemForm'
import { layoutClasses } from '../utils/layout'

export function AddItemPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const handleSubmit = async (data: any) => {
    setLoading(true)
    setError(null)
    
    try {
      // TODO: Implement actual API call to add item
      console.log('Adding item:', data)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Navigate back to closet after successful addition
      navigate('/closet')
    } catch (err: any) {
      setError(err.message || 'Failed to add item')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={layoutClasses.pageContainer}>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Add New Item</h1>
        <button
          onClick={() => navigate('/closet')}
          className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
        >
          ← Back to Closet
        </button>
      </div>
      
      <div className="max-w-2xl">
        <AddItemForm
          onSubmit={handleSubmit}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  )
}
