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
