import { useCloset } from '../hooks/useCloset'
import { Spinner, Button } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'
import { Link } from 'react-router-dom'

export function ClosetPage() {
  const { data, isLoading, error } = useCloset()
  return (
    <div className={layoutClasses.pageContainer}>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Closet</h1>
        <Link to="/closet/add">
          <Button>Add Item</Button>
        </Link>
      </div>
      {isLoading && (
        <div className={layoutClasses.inlineGroup + ' text-sm text-neutral-500'}>
          <Spinner size="sm" />
          Loading items…
        </div>
      )}
      <ErrorMessage error={error?.message} fallback="Failed to load closet items" />
      {data && data.length === 0 && (
        <div className="text-sm text-neutral-600">
          No items yet. <Link to="/closet/add" className="text-neutral-900 underline">Add your first item</Link> to get started!
        </div>
      )}
      {data && data.length > 0 && (
        <ul className={layoutClasses.gridResponsive}>
          {data.map(item => (
            <li key={item.id} className="border border-neutral-200 rounded-sm overflow-hidden bg-white">
              <div className="aspect-[4/5] bg-neutral-100 flex items-center justify-center overflow-hidden">
                <img src={item.image_url} alt={item.category} className="h-full w-full object-cover" />
              </div>
              <div className={layoutClasses.cardSmall.replace('border border-neutral-200 rounded-sm ', '') + ' space-y-1'}>
                <div className="text-sm font-medium capitalize tracking-tight">{item.category}</div>
                <div className={layoutClasses.metadata}>
                  {item.color && <span>{item.color}</span>}
                  {item.size && <span>{item.size}</span>}
                  {item.brand && <span>{item.brand}</span>}
                </div>
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {item.tags.slice(0,4).map(t => (
                      <span key={t} className={layoutClasses.badgeSmall}>{t}</span>
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
