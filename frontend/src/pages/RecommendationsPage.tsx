import { useRecommendations } from '../hooks/useRecommendations'
import { Spinner } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'

export function RecommendationsPage() {
  const { data, isLoading, error } = useRecommendations()

  return (
    <div className={layoutClasses.pageContainer}>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Recommendations</h1>
      </div>
      
      {isLoading && (
        <div className={layoutClasses.inlineGroup + ' text-sm text-neutral-500'}>
          <Spinner size="sm" />
          Generating recommendations…
        </div>
      )}
      
      <ErrorMessage error={error?.message} fallback="Failed to load recommendations" />
      
      {data && data.length === 0 && (
        <div className="text-sm text-neutral-600">No recommendations available yet.</div>
      )}
      
      {data && data.length > 0 && (
        <ul className={layoutClasses.listVerticalLarge}>
          {data.map(rec => (
            <li key={rec.id} className={layoutClasses.card}>
              <div className="flex items-start justify-between mb-3">
                <div className="space-y-1">
                  <div className={layoutClasses.inlineGroup}>
                    <span className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                      {rec.occasion || 'General'}
                    </span>
                    <span className="text-xs text-neutral-400">
                      {Math.round(rec.confidence_score * 100)}% match
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {rec.style_tags.map(tag => (
                      <span key={tag} className={layoutClasses.badge}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                {rec.outfit_items.map(item => (
                  <div key={item.id} className="flex-shrink-0">
                    <div className="w-20 h-24 bg-neutral-100 rounded-sm overflow-hidden">
                      <img 
                        src={item.image_url} 
                        alt={item.category}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="mt-1 text-xs text-neutral-600 text-center">
                      {item.category}
                    </div>
                  </div>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
