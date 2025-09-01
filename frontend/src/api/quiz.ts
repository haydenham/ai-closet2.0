import { api } from './client'

export interface QuizClothingItem {
  id: string
  name: string
  image_url: string
  gender: string
  category: string
  features: string[]
  auto_extracted_features?: string[]
  selection_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface QuizClothingItemsResponse {
  category: string
  items: QuizClothingItem[]
}

export interface QuizQuestionsResponse {
  gender: string
  questions: Record<string, QuizClothingItemsResponse>
}

export interface QuizSubmissionData {
  gender: string
  selected_items: Record<string, string> // category -> item_id
  weights?: Record<string, number>
}

export interface StyleCategory {
  id: string
  name: string
  gender: string
  features: string[]
  ai_theme_prompt?: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface QuizResponse {
  id: string
  user_id: string
  selected_item_ids: string[]
  calculated_scores: Record<string, number>
  assigned_category: string
  assigned_category_id?: string
  confidence_score?: number
  user_satisfaction_rating?: number
  user_feedback_text?: string
  completed_at: string
  selected_items?: QuizClothingItem[]
  assigned_category_obj?: StyleCategory
  is_hybrid?: boolean
  hybrid_styles?: string[]
  primary_score?: number
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function fetchQuizQuestions(gender: 'male' | 'female'): Promise<QuizQuestionsResponse> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    return {
      gender,
      questions: {
        top: {
          category: 'top',
          items: [
            {
              id: 'mock-top-1',
              name: 'Casual T-Shirt',
              image_url: 'https://via.placeholder.com/150x200.png?text=T-Shirt',
              gender,
              category: 'top',
              features: ['casual', 'comfortable'],
              selection_count: 0,
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            {
              id: 'mock-top-2', 
              name: 'Dress Shirt',
              image_url: 'https://via.placeholder.com/150x200.png?text=Dress+Shirt',
              gender,
              category: 'top',
              features: ['formal', 'professional'],
              selection_count: 0,
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ]
        },
        bottom: {
          category: 'bottom',
          items: [
            {
              id: 'mock-bottom-1',
              name: 'Jeans',
              image_url: 'https://via.placeholder.com/150x200.png?text=Jeans',
              gender,
              category: 'bottom',
              features: ['casual', 'denim'],
              selection_count: 0,
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ]
        },
        shoes: {
          category: 'shoes',
          items: [
            {
              id: 'mock-shoes-1',
              name: 'Sneakers',
              image_url: 'https://via.placeholder.com/150x200.png?text=Sneakers',
              gender,
              category: 'shoes',
              features: ['casual', 'comfortable'],
              selection_count: 0,
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ]
        },
        layering: {
          category: 'layering',
          items: []
        },
        accessory: {
          category: 'accessory',
          items: []
        },
        complete_outfit: {
          category: 'complete_outfit',
          items: []
        }
      }
    }
  }
  
  const res = await api.get<QuizQuestionsResponse>(`/quiz/questions/${gender}`)
  return res.data
}

export async function submitQuiz(submission: QuizSubmissionData): Promise<QuizResponse> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 1500))
    return {
      id: 'mock-response-1',
      user_id: 'mock-user-1',
      selected_item_ids: Object.values(submission.selected_items),
      calculated_scores: {
        'casual': 0.8,
        'formal': 0.2,
        'bohemian': 0.1
      },
      assigned_category: 'Casual Chic',
      confidence_score: 0.85,
      completed_at: new Date().toISOString(),
      is_hybrid: false,
      hybrid_styles: [],
      primary_score: 0.8
    }
  }
  
  // Convert string IDs to UUID format for backend compatibility
  const backendSubmission = {
    gender: submission.gender,
    selected_items: submission.selected_items, // Backend will handle string to UUID conversion
    weights: submission.weights || {}
  }
  
  const res = await api.post<QuizResponse>('/quiz/submit', backendSubmission)
  return res.data
}

export async function getLatestQuizResponse(): Promise<QuizResponse | null> {
  if (USE_MOCKS) {
    return null
  }
  
  try {
    const res = await api.get<QuizResponse>('/quiz/responses/latest')
    return res.data
  } catch (err) {
    return null
  }
}
