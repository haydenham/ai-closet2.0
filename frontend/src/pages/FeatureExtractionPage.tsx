import { useState } from 'react'
import { useFeatureExtraction } from '../hooks/useFeatureExtraction'
import { Button, Spinner } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'

export function FeatureExtractionPage() {
  const [urls, setUrls] = useState('')
  const mutation = useFeatureExtraction()

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const image_urls = urls.split('\n').map(s => s.trim()).filter(Boolean)
    mutation.mutate({ image_urls })
  }

  return (
    <div className={layoutClasses.pageContainer}>
      <h1 className="text-xl font-semibold tracking-tight">Feature Extraction</h1>
      <form onSubmit={onSubmit} className="space-y-4 max-w-xl">
        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium">Image URLs (one per line)</label>
          <textarea
            value={urls}
            onChange={e => setUrls(e.target.value)}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 resize-y min-h-[140px]"
            placeholder="https://example.com/image1.jpg&#10;https://example.com/image2.jpg"
          />
        </div>
        <Button
          type="submit"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <div className={layoutClasses.inlineGroup}>
              <Spinner size="sm" />
              Extracting…
            </div>
          ) : (
            'Extract Features'
          )}
        </Button>
      </form>
      <ErrorMessage error={mutation.error?.message} />
      {mutation.isSuccess && (
        <div className={layoutClasses.section}>
          <h2 className="text-sm font-medium uppercase tracking-wide text-neutral-500">Results</h2>
          <ul className={layoutClasses.listVertical + ' text-sm'}>
            {mutation.data.map(item => (
              <li key={item.item_id} className={layoutClasses.cardSmall}>
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
