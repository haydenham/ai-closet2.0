import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useRecommendations } from '../hooks/useRecommendations'
import { Spinner } from '../components/ui'
import { ErrorMessage } from '../components/ui/Alert'
import { GenerateRecommendations } from '../components/GenerateRecommendations'
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
  const [userGender, setUserGender] = useState<string | null>(null)

  // Debug logging
  console.log('🎯 RecommendationsPage render:', {
    dataLength: data?.length,
    isLoading,
    error: error?.message,
    generating
  })

  // Fetch user profile and quiz results
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Get user profile for gender
        const profileResponse = await api.get('/users/me')
        if (profileResponse.data?.gender) {
          setUserGender(profileResponse.data.gender)
        }

        // Get quiz results for style
        const quizResponse = await api.get('/quiz/results/latest')
        if (quizResponse.data?.primary_style) {
          setUserStyle(quizResponse.data.primary_style)
        }
      } catch (err) {
        console.log('Could not fetch user data:', err)
      }
    }
    fetchUserData()
  }, [])

  const handleGenerate = async (prompt: string) => {
    console.log('🚀 Generating recommendation with prompt:', prompt)
    
    // Check authentication
    const token = localStorage.getItem('auth_token')
    console.log('🔑 Auth token present:', !!token)
    
    setGenerating(true)
    setGenerateError(null)
    
    try {
      // Call the simplified API - backend will auto-inject gender, style, weather
      const response = await api.post('/outfit-recommendations/generate', {
        prompt: prompt
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
    <div className="min-h-screen bg-neutral-50">
      {/* Clean header - fixed at top */}
      <div className="sticky top-0 z-10 bg-white border-b border-neutral-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-lg font-medium">Outfit Generator</h1>
        </div>
      </div>
      
      {/* Main content area */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Generate New Recommendations - ChatGPT style input */}
        <GenerateRecommendations 
          onGenerate={handleGenerate}
          loading={generating}
          error={generateError}
          userStyle={userStyle}
          userGender={userGender}
        />
        
        {/* Divider */}
        {data && data.length > 0 && (
          <div className="my-12 border-t border-neutral-200"></div>
        )}
        
        {/* Existing Recommendations - cleaner card design */}
        {isLoading && (
          <div className="flex items-center justify-center py-12 text-neutral-500">
            <Spinner size="sm" />
            <span className="ml-2 text-sm">Loading recommendations…</span>
          </div>
        )}
        
        <ErrorMessage error={error?.message} fallback="Failed to load recommendations" />
        
        {data && data.length === 0 && !generating && (
          <div className="text-center py-12 text-neutral-500 text-sm">
            No recommendations yet. Try generating your first outfit above! ✨
          </div>
        )}
        
        {data && data.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wide">Recent Outfits</h2>
            
            <div className="space-y-4">
              {data.map(rec => (
                <div key={rec.id} className="bg-white rounded-xl border border-neutral-200 p-6 hover:shadow-md transition-shadow">
                  {/* Header with prompt */}
                  {rec.prompt && (
                    <div className="mb-4">
                      <p className="text-neutral-900 text-[15px] leading-relaxed">"{rec.prompt}"</p>
                    </div>
                  )}
                  
                  {/* Metadata badges */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {rec.occasion && (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-neutral-100 text-neutral-600 border border-neutral-200">
                        {rec.occasion}
                      </span>
                    )}
                    {rec.weather && (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-neutral-100 text-neutral-600 border border-neutral-200">
                        {rec.weather}
                      </span>
                    )}
                    {rec.similarity_scores?.overall_score && (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-green-50 text-green-700 border border-green-200">
                        {Math.round(rec.similarity_scores.overall_score * 100)}% match
                      </span>
                    )}
                  </div>
                  
                  {/* Outfit components */}
                  {rec.outfit_components && (
                    <div className="mb-4">
                      <div className="flex flex-wrap gap-2">
                        {rec.outfit_components.top && (
                          <div className="bg-neutral-50 px-3 py-2 rounded-lg text-sm text-neutral-700">
                            👕 {rec.outfit_components.top.type}
                          </div>
                        )}
                        {rec.outfit_components.bottom && (
                          <div className="bg-neutral-50 px-3 py-2 rounded-lg text-sm text-neutral-700">
                            👖 {rec.outfit_components.bottom.type}
                          </div>
                        )}
                        {rec.outfit_components.shoes && (
                          <div className="bg-neutral-50 px-3 py-2 rounded-lg text-sm text-neutral-700">
                            👟 {rec.outfit_components.shoes.type}
                          </div>
                        )}
                        {rec.outfit_components.outerwear && (
                          <div className="bg-neutral-50 px-3 py-2 rounded-lg text-sm text-neutral-700">
                            🧥 {rec.outfit_components.outerwear.type}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Matched items from closet */}
                  {rec.recommended_items && rec.recommended_items.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                        From your closet ({rec.item_count} items)
                      </h4>
                      <div className="flex gap-3 overflow-x-auto pb-2">
                        {rec.recommended_items.map(item => (
                          <div key={item.id} className="flex-shrink-0">
                            <div className="w-24 h-28 bg-neutral-100 rounded-lg overflow-hidden relative border border-neutral-200">
                              <img 
                                src={item.image_url} 
                                alt={item.name}
                                className="w-full h-full object-cover"
                              />
                            </div>
                            <div className="mt-2 text-xs text-neutral-600 max-w-[96px] truncate">
                              {item.name}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
