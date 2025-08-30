import { useQuery } from '@tanstack/react-query'
import { fetchClosetItems, ClosetItem } from '../api/closet'

export function useCloset() {
  return useQuery<ClosetItem[], Error>({
    queryKey: ['closet','items'],
    queryFn: fetchClosetItems
  })
}
