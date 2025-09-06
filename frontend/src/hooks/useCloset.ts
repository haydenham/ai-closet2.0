import { useQuery } from '@tanstack/react-query'
import { fetchClosetItems, ClosetItem } from '../api/closet'

export function useCloset() {
  const query = useQuery<ClosetItem[], Error>({
    queryKey: ['closet','items'],
    queryFn: fetchClosetItems
  })
  
  return {
    ...query,
    mutate: query.refetch
  }
}
