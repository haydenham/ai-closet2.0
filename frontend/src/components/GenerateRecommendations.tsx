import React, { useState } from 'react'
import { Button, Input } from '../components/ui'
import { ErrorMessage, Alert } from '../components/ui/Alert'
import { layoutClasses } from '../utils/layout'

interface RecommendationRequest {
  occasion: string
  weather: string
  style_preference: string
  color_preference: string
  specific_request: string
}

interface GenerateRecommendationsProps {
  onGenerate: (request: RecommendationRequest) => Promise<void>
  loading?: boolean
  error?: string | null
}

const OCCASIONS = [
  'Work/Professional',
  'Casual/Everyday', 
  'Date Night',
  'Party/Event',
  'Workout/Gym',
  'Travel',
  'Beach/Vacation',
  'Formal Event',
  'Weekend Errands',
  'Other'
]

const WEATHER_OPTIONS = [
  'Hot & Sunny',
  'Warm & Pleasant', 
  'Cool & Breezy',
  'Cold & Chilly',
  'Rainy',
  'Snowy',
  'Indoor/Climate Controlled'
]

const STYLE_PREFERENCES = [
  'Minimalist',
  'Bohemian', 
  'Classic/Timeless',
  'Trendy/Fashion Forward',
  'Sporty/Athletic',
  'Romantic/Feminine',
  'Edgy/Alternative',
  'Preppy',
  'Comfort First'
]

export const GenerateRecommendations: React.FC<GenerateRecommendationsProps> = ({
  onGenerate,
  loading = false,
  error = null
}) => {
  const [request, setRequest] = useState<RecommendationRequest>({
    occasion: '',
    weather: '',
    style_preference: '',
    color_preference: '',
    specific_request: ''
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

  const isValid = request.occasion && request.weather

  return (
    <div className={layoutClasses.section}>
      <Alert variant="info" className="mb-6">
        <div className="space-y-1">
          <div className="font-medium">Get AI-Powered Outfit Recommendations</div>
          <div className="text-sm">Tell Nomi about your plans and preferences, and get personalized outfit suggestions from your closet.</div>
        </div>
      </Alert>

      <form onSubmit={handleSubmit} className={layoutClasses.form}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              What's the occasion? *
            </label>
            <select
              value={request.occasion}
              onChange={handleInputChange('occasion')}
              required
              disabled={loading}
              className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 bg-white"
            >
              <option value="">Select occasion</option>
              {OCCASIONS.map(occasion => (
                <option key={occasion} value={occasion}>{occasion}</option>
              ))}
            </select>
          </div>

          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              What's the weather like? *
            </label>
            <select
              value={request.weather}
              onChange={handleInputChange('weather')}
              required
              disabled={loading}
              className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 bg-white"
            >
              <option value="">Select weather</option>
              {WEATHER_OPTIONS.map(weather => (
                <option key={weather} value={weather}>{weather}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className={layoutClasses.formField}>
            <label className="block text-sm font-medium text-neutral-700">
              Style Preference <span className="text-neutral-500 font-normal">(Optional)</span>
            </label>
            <select
              value={request.style_preference}
              onChange={handleInputChange('style_preference')}
              disabled={loading}
              className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 bg-white"
            >
              <option value="">Any style</option>
              {STYLE_PREFERENCES.map(style => (
                <option key={style} value={style}>{style}</option>
              ))}
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
              placeholder="e.g., bright colors, pastels, neutrals"
              disabled={loading}
            />
          </div>
        </div>

        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium text-neutral-700">
            Anything specific? <span className="text-neutral-500 font-normal">(Optional)</span>
          </label>
          <textarea
            value={request.specific_request}
            onChange={handleInputChange('specific_request')}
            placeholder="e.g., 'I want to look professional but approachable' or 'Something comfortable for walking around the city'"
            disabled={loading}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 resize-y min-h-[80px]"
          />
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
