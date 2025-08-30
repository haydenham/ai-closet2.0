/// <reference types="vitest" />
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCloset } from '../useCloset'
import React from 'react'

    vi.mock('../../api/closet', () => ({
  fetchClosetItems: async () => [{ id: '1', image_url: 'x', category: 'top' }]
}))
import { describe, expect, it, vi } from 'vitest'

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('useCloset', () => {
  it('returns items', async () => {
    const { result } = renderHook(() => useCloset(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.[0].category).toBe('top')
  })
})
