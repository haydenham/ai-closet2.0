import { useNavigate } from 'react-router-dom'
import { AddItemForm } from '../components/AddItemForm'
import { useAddClosetItem } from '../hooks/useAddClosetItem'
import { layoutClasses } from '../utils/layout'

export function AddItemPage() {
  const navigate = useNavigate()
  const addItemMutation = useAddClosetItem()

  const handleSubmit = async (data: any) => {
    try {
      await addItemMutation.mutateAsync(data)
      // Navigate back to closet after successful addition
      navigate('/closet')
    } catch (error) {
      // Error is handled by the mutation's error state
      console.error('Failed to add item:', error)
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
      
      <div className="bg-blue-50 border border-blue-200 rounded-sm p-4 mb-6">
        <div className="flex items-start space-x-3">
          <div className="text-blue-500 text-lg">🤖</div>
          <div>
            <div className="text-sm font-medium text-blue-900">AI-Powered Fashion Analysis</div>
            <div className="text-sm text-blue-700 mt-1">
              Upload an image and our Fashion-CLIP AI will automatically detect categories, styles, materials, colors, and brands!
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-2xl">
        <AddItemForm
          onSubmit={handleSubmit}
          loading={addItemMutation.isPending}
          error={addItemMutation.error?.message || null}
        />
      </div>
    </div>
  )
}
