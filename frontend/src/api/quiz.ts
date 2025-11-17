import { api } from './client'

export interface QuizClothingItem {
  id: string
  name: string | null
  image_url: string
  question_type: string
  style_category: string
  gender: string
  display_order: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface QuizQuestionType {
  question_text: string
  items: QuizClothingItem[]
}

export interface QuizQuestionsResponse {
  gender: string
  questions: Record<string, QuizQuestionType>
}

export interface QuizSubmissionData {
  gender: string
  selections: Record<string, string> // question_type -> item_id (pants, shirt, shorts, overlayer, shoes)
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
  primary_style: string
  secondary_style?: string | null
  style_message: string
  scores: Record<string, number>
  completed_at: string
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

export async function fetchQuizQuestions(gender: 'male' | 'female'): Promise<QuizQuestionsResponse> {
  if (USE_MOCKS) {
    await new Promise(r => setTimeout(r, 500))
    const mockStyles = ['Bohemian', 'Streetwear', 'Classic', 'Feminine', 'Edgy', 'Athleisure', 'Vintage', 'Glamorous', 'Eclectic', 'Minimalist']
    
    return {
      gender,
      questions: {
        pants: {
          question_text: 'Select the pants you would most want to wear',
          items: mockStyles.map((style, i) => ({
            id: `mock-pants-${i}`,
            name: `${style} Pants`,
            image_url: `https://via.placeholder.com/400x600.png?text=${style}+Pants`,
            question_type: 'pants',
            style_category: style,
            gender,
            display_order: i,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }))
        },
        shirt: {
          question_text: 'Select the top you would most want to wear',
          items: mockStyles.map((style, i) => ({
            id: `mock-shirt-${i}`,
            name: `${style} Shirt`,
            image_url: `https://via.placeholder.com/400x600.png?text=${style}+Shirt`,
            question_type: 'shirt',
            style_category: style,
            gender,
            display_order: i,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }))
        },
        shorts: {
          question_text: 'Select the shorts you would most want to wear',
          items: mockStyles.map((style, i) => ({
            id: `mock-shorts-${i}`,
            name: `${style} Shorts`,
            image_url: `https://via.placeholder.com/400x600.png?text=${style}+Shorts`,
            question_type: 'shorts',
            style_category: style,
            gender,
            display_order: i,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }))
        },
        overlayer: {
          question_text: 'Select the jacket you would most want to wear',
          items: mockStyles.map((style, i) => ({
            id: `mock-overlayer-${i}`,
            name: `${style} Jacket`,
            image_url: `https://via.placeholder.com/400x600.png?text=${style}+Jacket`,
            question_type: 'overlayer',
            style_category: style,
            gender,
            display_order: i,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }))
        },
        shoes: {
          question_text: 'Select the shoes you would most want to wear',
          items: mockStyles.map((style, i) => ({
            id: `mock-shoes-${i}`,
            name: `${style} Shoes`,
            image_url: `https://via.placeholder.com/400x600.png?text=${style}+Shoes`,
            question_type: 'shoes',
            style_category: style,
            gender,
            display_order: i,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }))
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
      primary_style: 'Bohemian',
      secondary_style: 'Classic',
      style_message: 'Bohemian with a hint of Classic',
      scores: {
        'Bohemian': 2,
        'Classic': 2,
        'Streetwear': 1
      },
      completed_at: new Date().toISOString()
    }
  }
  
  // Submit to backend - backend expects "selections" key
  const res = await api.post<QuizResponse>('/quiz/submit', submission)
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
