import { api } from './client'

// Data shapes (align loosely with backend Pydantic models; refine once full schemas are referenced)
export interface FeatureExtractionRequest {
  image_urls: string[]
}

export interface FeatureExtractionResult {
  item_id: string
  features: Record<string, number | string | boolean>
  status: string
}

export async function extractFeatures(data: FeatureExtractionRequest) {
  const res = await api.post<FeatureExtractionResult[]>('/feature-learning/extract-features', data)
  return res.data
}

export interface SatisfactionTrackingRequest {
  item_id: string
  satisfied: boolean
}

export async function trackSatisfaction(data: SatisfactionTrackingRequest) {
  const res = await api.post<{ success: boolean }>('/feature-learning/track-satisfaction', data)
  return res.data
}

export interface ItemLearningDatum {
  item_id: string
  views: number
  positive_feedback: number
  negative_feedback: number
  last_interaction?: string
}

export async function getItemLearningData(itemId: string) {
  const res = await api.get<ItemLearningDatum>(`/feature-learning/item-learning-data/${itemId}`)
  return res.data
}
