import { useQuery } from '@tanstack/react-query'
import { fetchRecommendations, Recommendation } from '../api/recommendations'

export function useRecommendations() {
  return useQuery<Recommendation[], Error>({
    queryKey: ['recommendations'],
    queryFn: fetchRecommendations
  })
}
