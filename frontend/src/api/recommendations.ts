import { api } from './client'

export interface ClothingItemResponse {
  id: string
  name: string
  image_url: string
  category: string
  color?: string
  brand?: string
  features?: string[]
}

export interface SimilarityScores {
  overall_score?: number
  color_harmony?: number
  style_consistency?: number
  weather_appropriateness?: number
}

export interface Recommendation {
  id: string
  user_id: string
  ai_response: string
  outfit_components?: {
    top?: { type: string; features: string[] }
    bottom?: { type: string; features: string[] }
    shoes?: { type: string; features: string[] }
    accessories?: { type: string; features: string[] }[]
    outerwear?: { type: string; features: string[] }
  }
  ai_model_used: string
  prompt: string
  occasion?: string
  weather?: string
  season?: string
  feedback_score?: number
  feedback_comments?: string
  is_favorite: boolean
  is_archived: boolean
  processing_time_ms?: number
  similarity_scores?: SimilarityScores
  created_at: string
  updated_at: string
  recommended_items: ClothingItemResponse[]
  item_count: number
  categories_covered: string[]
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function fetchRecommendations(): Promise<Recommendation[]> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 600))
    return [
      {
        id: 'rec-1',
        user_id: 'user-1',
        ai_response: 'Mock AI response',
        outfit_components: {
          top: { type: 'Performance Training Polo', features: ['mesh panels', 'UPF-rated', 'training-ready'] },
          bottom: { type: 'Athletic Shorts', features: ['moisture-wicking', 'stretchy', 'lightweight'] }
        },
        ai_model_used: 'gemini-pro',
        prompt: 'Generate a workout outfit',
        occasion: 'workout',
        weather: 'hot',
        feedback_score: undefined,
        feedback_comments: undefined,
        is_favorite: false,
        is_archived: false,
        processing_time_ms: 1500,
        similarity_scores: {
          overall_score: 0.85,
          color_harmony: 0.90,
          style_consistency: 0.88,
          weather_appropriateness: 0.95
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        recommended_items: [
          {
            id: 'item-1',
            name: 'Nike Training Polo',
            image_url: 'https://via.placeholder.com/120x150.png?text=Top',
            category: 'top',
            color: 'navy',
            features: ['mesh panels', 'training-ready']
          },
          {
            id: 'item-2',
            name: 'Adidas Athletic Shorts',
            image_url: 'https://via.placeholder.com/120x150.png?text=Shorts',
            category: 'bottom',
            color: 'black',
            features: ['moisture-wicking', 'stretchy', 'lightweight']
          }
        ],
        item_count: 2,
        categories_covered: ['top', 'bottom']
      }
    ]
  }
  
  console.log('🔍 Fetching recommendations from API...')
  try {
    const res = await api.get<Recommendation[]>('/outfit-recommendations/history')
    console.log('✅ API Response:', res.data)
    console.log('📊 Number of recommendations:', res.data.length)
    
    if (res.data.length > 0) {
      console.log('📝 First recommendation:', res.data[0])
    } else {
      console.log('❌ No recommendations found in response')
    }
    
    return res.data
  } catch (error) {
    console.error('❌ Error fetching recommendations:', error)
    throw error
  }
}
