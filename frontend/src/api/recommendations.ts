import { api } from './client'

export interface Recommendation {
  id: string
  outfit_items: {
    id: string
    image_url: string
    category: string
    color?: string
  }[]
  confidence_score: number
  style_tags: string[]
  occasion?: string
  created_at: string
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function fetchRecommendations(): Promise<Recommendation[]> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 600))
    return [
      {
        id: 'rec-1',
        outfit_items: [
          { id: 'item-1', image_url: 'https://via.placeholder.com/120x150.png?text=Top', category: 'top', color: 'white' },
          { id: 'item-2', image_url: 'https://via.placeholder.com/120x150.png?text=Pants', category: 'pants', color: 'black' }
        ],
        confidence_score: 0.85,
        style_tags: ['casual', 'classic'],
        occasion: 'work',
        created_at: new Date().toISOString()
      },
      {
        id: 'rec-2', 
        outfit_items: [
          { id: 'item-3', image_url: 'https://via.placeholder.com/120x150.png?text=Dress', category: 'dress', color: 'navy' },
          { id: 'item-4', image_url: 'https://via.placeholder.com/120x150.png?text=Shoes', category: 'shoes', color: 'brown' }
        ],
        confidence_score: 0.92,
        style_tags: ['elegant', 'formal'],
        occasion: 'dinner',
        created_at: new Date().toISOString()
      }
    ]
  }
  const res = await api.get<Recommendation[]>('/outfit-recommendations')
  return res.data
}
