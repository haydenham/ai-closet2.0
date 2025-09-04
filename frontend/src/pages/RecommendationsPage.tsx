import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useRecommendations } from '../hooks/useRecommendations'
import { Spinner } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { GenerateRecommendations } from '../components/GenerateRecommendations'
import { layoutClasses } from '../utils/layout'
import { useState } from 'react'
import { api } from '../api/client'
import { getToken } from '../api/auth'

export function RecommendationsPage() {
  // Check if user is authenticated
  const token = getToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  const { data, isLoading, error, refetch } = useRecommendations()
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [userStyle, setUserStyle] = useState<string | null>(null)

  // Debug logging
  console.log('🎯 RecommendationsPage render:', {
    dataLength: data?.length,
    isLoading,
    error: error?.message,
    generating
  })

  // Fetch user's quiz results to get their style
  useEffect(() => {
    const fetchUserStyle = async () => {
      try {
        const response = await api.get('/quiz/responses/latest')
        if (response.data?.assigned_category) {
          setUserStyle(response.data.assigned_category)
        }
      } catch (err) {
        console.log('No quiz results found - user can take quiz to get personalized recommendations')
      }
    }
    fetchUserStyle()
  }, [])

  const handleGenerate = async (request: any) => {
    console.log('🚀 Generating recommendation with request:', request)
    
    // Check authentication
    const token = localStorage.getItem('auth_token')
    console.log('🔑 Auth token present:', !!token)
    console.log('🔑 Token length:', token?.length || 0)
    
    setGenerating(true)
    setGenerateError(null)
    
    try {
      // Call the actual recommendation API with closet matching
      const response = await api.post('/outfit-recommendations/generate-and-match', {
        occasion: request.occasion,
        user_request: request.user_request,
        color_preference: request.color_preference,
        weather: request.weather
      })
      
      console.log('✅ Generated recommendation response:', response.data)
      
      // Refresh recommendations after generation
      console.log('🔄 Refreshing recommendations...')
      await refetch()
      console.log('✅ Recommendations refreshed')
      
    } catch (err: any) {
      console.error('❌ Recommendation generation error:', err)
      console.error('❌ Error status:', err.response?.status)
      console.error('❌ Error data:', err.response?.data)
      setGenerateError(err.response?.data?.detail || err.message || 'Failed to generate recommendations')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className={layoutClasses.pageContainer}>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Recommendations</h1>
      </div>
      
      {/* Generate New Recommendations */}
      <GenerateRecommendations 
        onGenerate={handleGenerate}
        loading={generating}
        error={generateError}
        userStyle={userStyle}
      />
      
      {/* Existing Recommendations */}
      <div>
        <h2 className="text-lg font-medium tracking-tight mb-4">Your Recent Recommendations</h2>
        
        {isLoading && (
          <div className={layoutClasses.inlineGroup + ' text-sm text-neutral-500'}>
            <Spinner size="sm" />
            Loading recommendations…
          </div>
        )}
        
        <ErrorMessage error={error?.message} fallback="Failed to load recommendations" />
        
        {data && data.length === 0 && (
          <div className="text-sm text-neutral-600">
            No recommendations yet. Generate your first recommendation above!
          </div>
        )}
        
        {data && data.length > 0 && (
          <ul className={layoutClasses.listVerticalLarge}>
            {data.map(rec => (
              <li key={rec.id} className={layoutClasses.card}>
                <div className="flex items-start justify-between mb-4">
                  <div className="space-y-2">
                    <div className={layoutClasses.inlineGroup}>
                      <span className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                        {rec.occasion || 'General'}
                      </span>
                      <span className="text-xs text-neutral-400">
                        {rec.weather && `${rec.weather} weather`}
                      </span>
                      <span className="text-xs text-neutral-400">
                        {rec.ai_model_used}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {rec.similarity_scores?.overall_score && (
                        <span className={layoutClasses.badge + ' bg-green-100 text-green-800'}>
                          {Math.round(rec.similarity_scores.overall_score * 100)}% match
                        </span>
                      )}
                      {rec.similarity_scores?.style_consistency && (
                        <span className={layoutClasses.badge + ' bg-blue-100 text-blue-800'}>
                          Style: {Math.round(rec.similarity_scores.style_consistency * 100)}%
                        </span>
                      )}
                      {rec.similarity_scores?.color_harmony && (
                        <span className={layoutClasses.badge + ' bg-purple-100 text-purple-800'}>
                          Colors: {Math.round(rec.similarity_scores.color_harmony * 100)}%
                        </span>
                      )}
                      {rec.similarity_scores?.weather_appropriateness && (
                        <span className={layoutClasses.badge + ' bg-orange-100 text-orange-800'}>
                          Weather: {Math.round(rec.similarity_scores.weather_appropriateness * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* AI Recommendation vs Your Closet */}
                <div className="space-y-4">
                  {rec.outfit_components && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-700 mb-2">AI Recommendation</h4>
                      <div className="flex gap-2 text-xs text-neutral-600">
                        {rec.outfit_components.top && (
                          <span className="bg-neutral-100 px-2 py-1 rounded">
                            {rec.outfit_components.top.type}
                          </span>
                        )}
                        {rec.outfit_components.bottom && (
                          <span className="bg-neutral-100 px-2 py-1 rounded">
                            {rec.outfit_components.bottom.type}
                          </span>
                        )}
                        {rec.outfit_components.shoes && (
                          <span className="bg-neutral-100 px-2 py-1 rounded">
                            {rec.outfit_components.shoes.type}
                          </span>
                        )}
                        {rec.outfit_components.outerwear && (
                          <span className="bg-neutral-100 px-2 py-1 rounded">
                            {rec.outfit_components.outerwear.type}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {rec.recommended_items && rec.recommended_items.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-700 mb-2">
                        Matched from Your Closet ({rec.item_count} items)
                      </h4>
                      <div className="flex gap-3">
                        {rec.recommended_items.map(item => (
                          <div key={item.id} className="flex-shrink-0">
                            <div className="w-20 h-24 bg-neutral-100 rounded-sm overflow-hidden relative">
                              <img 
                                src={item.image_url} 
                                alt={item.name}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute top-1 right-1 bg-green-500 text-white text-xs px-1 rounded">
                                ✓
                              </div>
                            </div>
                            <div className="mt-1 text-xs text-neutral-600 text-center">
                              {item.name}
                            </div>
                            <div className="text-xs text-neutral-500 text-center">
                              {item.category}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Categories Covered */}
                  {rec.categories_covered && rec.categories_covered.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-700 mb-2">Categories Covered</h4>
                      <div className="flex flex-wrap gap-1">
                        {rec.categories_covered.map(category => (
                          <span key={category} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            {category}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* User Prompt */}
                  {rec.prompt && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-700 mb-1">Request</h4>
                      <p className="text-sm text-neutral-600 italic">"{rec.prompt}"</p>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
