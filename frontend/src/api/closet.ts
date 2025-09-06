import { api } from './client'

export interface ClosetItem {
  id: string
  image_url: string
  category: string
  color?: string | null
  brand?: string | null
  size?: string | null
  tags?: string[] | null
  upload_date?: string
  filename?: string
  original_filename?: string
  description?: string | null
  file_size?: number
  image_width?: number
  image_height?: number
}

export interface AddItemData {
  category: string
  color: string
  brand?: string
  size?: string
  notes?: string
  files: File[]
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function fetchClosetItems(): Promise<ClosetItem[]> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 40))
    return [
      {
        id: 'mock-1',
        image_url: 'https://via.placeholder.com/160x200.png?text=Top',
        category: 'top',
        color: 'black',
        brand: 'MockBrand',
        size: 'M',
        tags: ['casual', 'basic'],
        upload_date: new Date().toISOString()
      },
      {
        id: 'mock-2',
        image_url: 'https://via.placeholder.com/160x200.png?text=Pants',
        category: 'pants',
        color: 'indigo',
        brand: 'DenimCo',
        size: '32',
        tags: ['denim'],
        upload_date: new Date().toISOString()
      }
    ]
  }
  const res = await api.get<ClosetItem[]>('/closet/items')
  return res.data
}

export async function addClosetItem(data: AddItemData): Promise<ClosetItem> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 1000))
    return {
      id: `mock-${Date.now()}`,
      image_url: 'https://via.placeholder.com/160x200.png?text=New+Item',
      category: data.category,
      color: data.color,
      brand: data.brand || null,
      size: data.size || null,
      tags: null, // Tags will be auto-generated from description
      description: data.notes || null,
      upload_date: new Date().toISOString()
    }
  }

  // Create FormData for file upload
  const formData = new FormData()
  
  // Add the first file (for now, handle multiple files later)
  if (data.files.length > 0) {
    formData.append('file', data.files[0])
  }
  
  // Add form fields to match backend API
  formData.append('category', data.category)
  if (data.color) formData.append('color', data.color)
  if (data.brand) formData.append('brand', data.brand)
  if (data.size) formData.append('size', data.size)
  if (data.notes) formData.append('description', data.notes)
  
  // Tags will be auto-generated from description on the backend

  const res = await api.post<ClosetItem>('/closet/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return res.data
}

export async function updateClosetItem(id: string, updates: Partial<ClosetItem>): Promise<ClosetItem> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    return { id, ...updates } as ClosetItem
  }
  
  const res = await api.put<ClosetItem>(`/closet/items/${id}`, updates)
  return res.data
}

export async function deleteClosetItem(id: string): Promise<void> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    return
  }
  
  await api.delete(`/closet/items/${id}`)
}
