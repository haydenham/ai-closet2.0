import { useMutation, useQueryClient } from '@tanstack/react-query'
import { addClosetItem } from '../api/closet'

export function useAddClosetItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: addClosetItem,
    onSuccess: () => {
      // Invalidate and refetch closet items after successful addition
      queryClient.invalidateQueries({ queryKey: ['closet'] })
    },
  })
}
