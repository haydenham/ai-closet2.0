import { useCloset } from '../hooks/useCloset'

export function ClosetPage() {
  const { data, isLoading, isError, error } = useCloset()
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Closet</h1>
      </div>
      {isLoading && <div className="text-sm text-neutral-500">Loading items…</div>}
      {isError && <div className="text-sm text-red-600">{error?.message || 'Failed to load'}</div>}
      {data && data.length === 0 && (
        <div className="text-sm text-neutral-600">No items yet.</div>
      )}
      {data && data.length > 0 && (
        <ul className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {data.map(item => (
            <li key={item.id} className="border border-neutral-200 rounded-sm overflow-hidden bg-white">
              <div className="aspect-[4/5] bg-neutral-100 flex items-center justify-center overflow-hidden">
                <img src={item.image_url} alt={item.category} className="h-full w-full object-cover" />
              </div>
              <div className="p-3 space-y-1">
                <div className="text-sm font-medium capitalize tracking-tight">{item.category}</div>
                <div className="text-xs text-neutral-600 flex gap-2 flex-wrap">
                  {item.color && <span>{item.color}</span>}
                  {item.size && <span>{item.size}</span>}
                  {item.brand && <span>{item.brand}</span>}
                </div>
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {item.tags.slice(0,4).map(t => (
                      <span key={t} className="px-1.5 py-0.5 bg-neutral-100 text-neutral-700 rounded-sm text-[10px] tracking-wide uppercase">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
