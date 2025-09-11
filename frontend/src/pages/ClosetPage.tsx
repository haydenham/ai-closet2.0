import { useCloset } from '../hooks/useCloset'
import { Spinner, Button } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'
import { getCategoryDisplayName } from '../utils/categories'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { deleteClosetItem, updateClosetItem } from '../api/closet'

interface EditingItem {
  id: string
  description: string
  brand: string
  size: string
  color: string
}

export function ClosetPage() {
  const { data, isLoading, error, mutate } = useCloset()
  const [deletingItems, setDeletingItems] = useState<Set<string>>(new Set())
  const [editingItem, setEditingItem] = useState<EditingItem | null>(null)
  const [saving, setSaving] = useState(false)
  
  const handleDeleteItem = async (itemId: string) => {
    if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
      return
    }
    
    setDeletingItems(prev => new Set(prev).add(itemId))
    
    try {
      await deleteClosetItem(itemId)
      // Refresh the data after successful deletion
      mutate()
    } catch (error) {
      console.error('Failed to delete item:', error)
      alert('Failed to delete item. Please try again.')
    } finally {
      setDeletingItems(prev => {
        const next = new Set(prev)
        next.delete(itemId)
        return next
      })
    }
  }

  const handleEditItem = (item: any) => {
    setEditingItem({
      id: item.id,
      description: item.description || '',
      brand: item.brand || '',
      size: item.size || '',
      color: item.color || ''
    })
  }

  const handleSaveEdit = async () => {
    if (!editingItem) return
    
    setSaving(true)
    try {
      await updateClosetItem(editingItem.id, {
        description: editingItem.description.trim() || null,
        brand: editingItem.brand.trim() || null,
        size: editingItem.size.trim() || null,
        color: editingItem.color.trim() || null
      })
      setEditingItem(null)
      mutate()
    } catch (error) {
      console.error('Failed to update item:', error)
      alert('Failed to update item. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditingItem(null)
  }
  
  return (
    <div className={layoutClasses.pageContainer}>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Closet</h1>
        <Link to="/closet/add">
          <Button>Add Item</Button>
        </Link>
      </div>
      
      {isLoading && (
        <div className={layoutClasses.inlineGroup + ' text-sm text-neutral-500'}>
          <Spinner size="sm" />
          Loading items…
        </div>
      )}
      <ErrorMessage error={error?.message} fallback="Failed to load closet items" />
      {data && data.length === 0 && (
        <div className="text-sm text-neutral-600">
          No items yet. <Link to="/closet/add" className="text-neutral-900 underline">Add your first item</Link> to get started!
        </div>
      )}
      {data && data.length > 0 && (
        <ul className={layoutClasses.gridResponsive}>
          {data.map(item => {
            const isDeleting = deletingItems.has(item.id)
            const isEditing = editingItem?.id === item.id
            return (
              <li key={item.id} className="border border-neutral-200 rounded-sm overflow-hidden bg-white relative">
                <div className="aspect-[4/5] bg-neutral-100 flex items-center justify-center overflow-hidden">
                  <img src={item.image_url} alt={item.category} className="h-full w-full object-cover" />
                  {/* Action buttons overlay */}
                  <div className="absolute top-2 right-2 flex gap-1">
                    <button
                      onClick={() => handleEditItem(item)}
                      disabled={isDeleting || isEditing}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-2 py-1 rounded-sm opacity-80 hover:opacity-100 transition-opacity disabled:opacity-50"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      disabled={isDeleting}
                      className="bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded-sm opacity-80 hover:opacity-100 transition-opacity disabled:opacity-50"
                    >
                      {isDeleting ? '...' : '×'}
                    </button>
                  </div>
                </div>
                <div className={layoutClasses.cardSmall.replace('border border-neutral-200 rounded-sm ', '') + ' space-y-1'}>
                  {isEditing ? (
                    // Edit form
                    <div className="space-y-2">
                      <div className="text-sm font-medium tracking-tight">{getCategoryDisplayName(item.category)}</div>
                      
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={editingItem?.color || ''}
                          onChange={(e) => setEditingItem(prev => prev ? {...prev, color: e.target.value} : null)}
                          placeholder="Color"
                          className="w-full text-xs px-2 py-1 border border-neutral-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            type="text"
                            value={editingItem?.brand || ''}
                            onChange={(e) => setEditingItem(prev => prev ? {...prev, brand: e.target.value} : null)}
                            placeholder="Brand"
                            className="w-full text-xs px-2 py-1 border border-neutral-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                        
                        <textarea
                          value={editingItem?.description || ''}
                          onChange={(e) => setEditingItem(prev => prev ? {...prev, description: e.target.value} : null)}
                          placeholder="Optional description (personal notes, fit details, etc.)"
                          rows={3}
                          className="w-full text-xs px-2 py-1 border border-neutral-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                        />
                      </div>
                      
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={handleSaveEdit}
                          disabled={saving}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs px-2 py-1 rounded-sm disabled:opacity-50"
                        >
                          {saving ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          disabled={saving}
                          className="flex-1 bg-gray-500 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded-sm disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    // View mode
                    <>
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium tracking-tight">{getCategoryDisplayName(item.category)}</div>
                      </div>
                      <div className={layoutClasses.metadata}>
                        {item.color && <span>{item.color}</span>}
                        {item.size && <span>{item.size}</span>}
                        {item.brand && <span>{item.brand}</span>}
                      </div>
                      {item.description && (
                        <div className="text-xs text-neutral-600 bg-neutral-50 p-2 rounded-sm border border-neutral-200">
                          <div className="font-medium text-neutral-700 mb-1">📝 Notes:</div>
                          <div className="line-clamp-2">{item.description}</div>
                        </div>
                      )}
                      {item.tags && item.tags.length > 0 && (
                        <div className="pt-1">
                          <div className="text-xs text-neutral-500 mb-1">🤖 AI-detected features:</div>
                          <div className="flex flex-wrap gap-1">
                            {item.tags.slice(0,6).map(t => (
                              <span key={t} className={layoutClasses.badgeSmall}>{t}</span>
                            ))}
                            {item.tags.length > 6 && (
                              <span className="text-xs text-neutral-500">+{item.tags.length - 6} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
