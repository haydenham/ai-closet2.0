import { useState } from 'react'
import { useFeatureExtraction } from '../hooks/useFeatureExtraction'

export function FeatureExtractionPage() {
  const [urls, setUrls] = useState('')
  const mutation = useFeatureExtraction()

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const image_urls = urls.split('\n').map(s => s.trim()).filter(Boolean)
    mutation.mutate({ image_urls })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold tracking-tight">Feature Extraction</h1>
      <form onSubmit={onSubmit} className="space-y-4 max-w-xl">
        <div className="space-y-2">
          <label className="block text-sm font-medium">Image URLs (one per line)</label>
          <textarea
            value={urls}
            onChange={e => setUrls(e.target.value)}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 resize-y min-h-[140px]"
            placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg"
          />
        </div>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="h-9 px-4 rounded-sm bg-neutral-900 text-white text-sm font-medium tracking-tight disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-800 transition-colors"
        >
          {mutation.isPending ? 'Extracting…' : 'Extract Features'}
        </button>
      </form>
      {mutation.isError && (
        <div className="text-sm text-red-600">{mutation.error.message}</div>
      )}
      {mutation.isSuccess && (
        <div className="space-y-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-neutral-500">Results</h2>
          <ul className="space-y-3 text-sm">
            {mutation.data.map(item => (
              <li key={item.item_id} className="border border-neutral-200 rounded-sm p-3">
                <div className="font-medium mb-1">{item.item_id}</div>
                <pre className="text-xs bg-neutral-50 p-2 rounded overflow-x-auto">{JSON.stringify(item.features, null, 2)}</pre>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
