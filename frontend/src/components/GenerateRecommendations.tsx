import React, { useState } from 'react'
import { ErrorMessage } from '../components/ui/Alert'

interface GenerateRecommendationsProps {
  onGenerate: (prompt: string) => Promise<void>
  loading?: boolean
  error?: string | null
  userStyle?: string | null
  userGender?: string | null
}

export const GenerateRecommendations: React.FC<GenerateRecommendationsProps> = ({
  onGenerate,
  loading = false,
  error = null,
  userStyle = null,
  userGender = null
}) => {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      await onGenerate(prompt.trim())
    }
  }

  // Hardcoded weather for now
  const weather = {
    condition: 'warm',
    temperature: 72,
    emoji: '☀️'
  }

  const isValid = prompt.trim().length >= 10

  return (
    <div className="max-w-3xl mx-auto">
      {/* Clean header with context badges */}
      <div className="mb-8">
        <div className="flex flex-wrap gap-2 mb-6">
          {userStyle && (
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm bg-neutral-100 text-neutral-700 border border-neutral-200">
              {userStyle}
            </span>
          )}
          {userGender && (
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm bg-neutral-100 text-neutral-700 border border-neutral-200">
              {userGender === 'male' ? 'Men\'s' : 'Women\'s'}
            </span>
          )}
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm bg-neutral-100 text-neutral-700 border border-neutral-200">
            {weather.emoji} {weather.temperature}°F
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main input area - ChatGPT style */}
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your occasion and what you'd like to wear..."
            className="w-full px-4 py-4 pr-16 border border-neutral-300 rounded-2xl shadow-sm placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent resize-none text-[15px] leading-relaxed"
            rows={3}
            required
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && isValid && !loading) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
          />
          
          {/* Send button inside textarea */}
          <button
            type="submit"
            disabled={!isValid || loading}
            className={`absolute right-3 bottom-3 p-2 rounded-lg transition-all ${
              isValid && !loading
                ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <span className="inline-block animate-spin text-lg">🤖</span>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>

        {/* Character count - subtle */}
        <div className="flex items-center justify-between text-xs text-neutral-400 px-1">
          <div>
            {prompt.length > 0 && prompt.length < 10 && (
              <span className="text-neutral-500">Min 10 characters</span>
            )}
          </div>
          <div>{prompt.length} / 1000</div>
        </div>

        {/* Example prompts - collapsed by default, cleaner */}
        {prompt.length === 0 && (
          <div className="space-y-2 px-1">
            <p className="text-xs text-neutral-400">Try asking:</p>
            <div className="space-y-1.5">
              {[
                "Casual brunch with friends, something comfortable but chic",
                "Job interview at a tech company",
                "Date night at a nice restaurant",
                "Weekend errands, practical and easy"
              ].map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setPrompt(example)}
                  className="block text-left text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        <ErrorMessage error={error} />
      </form>
    </div>
  )
}
