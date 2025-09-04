import React, { useState } from 'react'
import { Button, Input } from '../components/ui'
import { ErrorMessage, Alert } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'

interface RecommendationRequest {
  occasion: string
  user_request: string
  color_preference?: string
  weather: string
}

interface GenerateRecommendationsProps {
  onGenerate: (request: RecommendationRequest) => Promise<void>
  loading?: boolean
  error?: string | null
  userStyle?: string | null  // From quiz results
}

export const GenerateRecommendations: React.FC<GenerateRecommendationsProps> = ({
  onGenerate,
  loading = false,
  error = null,
  userStyle = null
}) => {
  const [request, setRequest] = useState<RecommendationRequest>({
    occasion: '',
    user_request: '',
    color_preference: '',
    weather: 'warm'
  })

  const handleInputChange = (field: keyof RecommendationRequest) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setRequest(prev => ({ ...prev, [field]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onGenerate(request)
  }

  const isValid = request.occasion && request.user_request && request.weather

  return (
    <div className={layoutClasses.section}>
      <Alert variant="info" className="mb-6">
        <div className="space-y-1">
          <div className="font-medium">Get AI-Powered Outfit Recommendations</div>
          <div className="text-sm">Tell Nomi about your plans and get personalized outfit suggestions from your closet.</div>
          {userStyle && (
            <div className="text-sm text-blue-600">Your style: {userStyle}</div>
          )}
        </div>
      </Alert>

      <form onSubmit={handleSubmit} className={layoutClasses.form}>
        <div className="space-y-4">
          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              What's the occasion? *
            </label>
            <Input
              type="text"
              value={request.occasion}
              onChange={handleInputChange('occasion')}
              placeholder="e.g., work meeting, date night, casual weekend, gym session"
              required
              disabled={loading}
            />
          </div>

          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              Describe what you want to wear *
            </label>
            <textarea
              value={request.user_request}
              onChange={handleInputChange('user_request')}
              placeholder="e.g., something professional but comfortable, a trendy outfit for brunch, casual and cozy for studying"
              className="w-full px-3 py-2 border border-neutral-300 rounded-md shadow-sm placeholder-neutral-400 focus:outline-none focus:ring-neutral-500 focus:border-neutral-500 min-h-[80px] resize-y"
              required
              disabled={loading}
            />
          </div>

          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              Weather/Temperature *
            </label>
            <select
              value={request.weather}
              onChange={handleInputChange('weather')}
              required
              disabled={loading}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md shadow-sm focus:outline-none focus:ring-neutral-500 focus:border-neutral-500"
            >
              <option value="hot">Hot (80°F+)</option>
              <option value="warm">Warm (65-80°F)</option>
              <option value="mild">Mild (50-65°F)</option>
              <option value="cold">Cold (Below 50°F)</option>
            </select>
          </div>

          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              Color Preference <span className="text-neutral-500 font-normal">(Optional)</span>
            </label>
            <Input
              type="text"
              value={request.color_preference}
              onChange={handleInputChange('color_preference')}
              placeholder="e.g., bright colors, pastels, neutrals, black and white"
              disabled={loading}
            />
          </div>
        </div>

        <ErrorMessage error={error} />

        <Button
          type="submit"
          disabled={loading || !isValid}
          className="w-full sm:w-auto"
          size="lg"
        >
          {loading ? 'Generating Recommendations...' : '✨ Get AI Recommendations'}
        </Button>
      </form>
    </div>
  )
}
