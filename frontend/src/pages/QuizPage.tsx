import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { Alert, ErrorMessage } from '../components/ui/Alert'
import { QuizClothingItem, fetchQuizQuestions, submitQuiz, QuizSubmissionData } from '../api/quiz'
import { layoutClasses } from '../utils/layout'

const CATEGORIES = ['top', 'bottom', 'shoes', 'layering', 'accessory', 'complete_outfit']

const CATEGORY_LABELS = {
  top: 'Tops',
  bottom: 'Bottoms', 
  shoes: 'Shoes',
  layering: 'Layering Pieces',
  accessory: 'Accessories',
  complete_outfit: 'Complete Outfits'
}

export function QuizPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<'gender' | 'quiz' | 'results'>('gender')
  const [gender, setGender] = useState<'male' | 'female' | null>(null)
  const [currentCategory, setCurrentCategory] = useState(0)
  const [questions, setQuestions] = useState<Record<string, QuizClothingItem[]>>({})
  const [selections, setSelections] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [countdown, setCountdown] = useState<number | null>(null)

  const handleGenderSelect = async (selectedGender: 'male' | 'female') => {
    setGender(selectedGender)
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetchQuizQuestions(selectedGender)
      
      // Convert to simpler format for UI
      const questionsData: Record<string, QuizClothingItem[]> = {}
      CATEGORIES.forEach(category => {
        questionsData[category] = response.questions[category]?.items || []
      })
      
      setQuestions(questionsData)
      setCurrentStep('quiz')
    } catch (err: any) {
      setError(err.message || 'Failed to load quiz questions')
    } finally {
      setLoading(false)
    }
  }

  const handleItemSelect = (category: string, itemId: string) => {
    setSelections(prev => ({
      ...prev,
      [category]: itemId
    }))
  }

  const handleNext = () => {
    if (currentCategory < CATEGORIES.length - 1) {
      setCurrentCategory(currentCategory + 1)
    } else {
      handleSubmit()
    }
  }

  const handlePrevious = () => {
    if (currentCategory > 0) {
      setCurrentCategory(currentCategory - 1)
    }
  }

  const handleSubmit = async () => {
    if (!gender) return
    
    setLoading(true)
    setError(null)
    
    try {
      const submission: QuizSubmissionData = {
        gender,
        selected_items: selections
      }
      
      console.log('Submitting quiz:', submission) // Debug
      const response = await submitQuiz(submission)
      console.log('Quiz response:', response) // Debug
      setResult(response)
      setCurrentStep('results')
      
      // Start countdown and auto-redirect
      setCountdown(5)
      const countdownInterval = setInterval(() => {
        setCountdown(prev => {
          if (prev === null || prev <= 1) {
            clearInterval(countdownInterval)
            navigate('/recommendations')
            return null
          }
          return prev - 1
        })
      }, 1000)
    } catch (err: any) {
      console.error('Quiz submission error:', err) // Debug
      setError(err.response?.data?.detail || err.message || 'Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  const currentCategoryName = CATEGORIES[currentCategory]
  const currentItems = questions[currentCategoryName] || []
  const selectedItemId = selections[currentCategoryName]
  const progress = ((currentCategory + 1) / CATEGORIES.length) * 100

  if (currentStep === 'gender') {
    return (
      <div className={layoutClasses.pageContainer}>
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-2xl font-bold mb-2">Style Quiz</h1>
          <p className="text-neutral-600 mb-8">
            Discover your personal style with our AI-powered quiz. Choose the items that resonate with you!
          </p>
          
          <div className="space-y-4">
            <h2 className="text-lg font-medium">What's your gender?</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant="outline" 
                size="lg"
                onClick={() => handleGenderSelect('female')}
                disabled={loading}
                className="h-20"
              >
                Female
              </Button>
              <Button
                variant="outline"
                size="lg" 
                onClick={() => handleGenderSelect('male')}
                disabled={loading}
                className="h-20"
              >
                Male
              </Button>
            </div>
          </div>
          
          <ErrorMessage error={error} className="mt-4" />
          
          {loading && (
            <div className="mt-4 text-sm text-neutral-600">
              Loading quiz questions...
            </div>
          )}
        </div>
      </div>
    )
  }

  if (currentStep === 'results') {
    return (
      <div className={layoutClasses.pageContainer}>
        <div className="max-w-md mx-auto text-center">
          <div className="mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">✨</span>
            </div>
            <h1 className="text-2xl font-bold mb-2">Your Style Profile</h1>
          </div>
          
          {result ? (
            <div className="space-y-4 text-left">
              <Alert variant="success">
                <div className="space-y-2">
                  <div className="font-medium text-lg">
                    {result.assigned_category || 'Your Style Profile'}
                  </div>
                  {result.confidence_score && (
                    <div className="text-sm">
                      Confidence: {Math.round(result.confidence_score * 100)}%
                    </div>
                  )}
                </div>
              </Alert>
              
              {result.is_hybrid && result.hybrid_styles?.length > 0 && (
                <Alert variant="info">
                  <div>
                    <div className="font-medium">Hybrid Style</div>
                    <div className="text-sm">
                      You have a mix of: {result.hybrid_styles.join(', ')}
                    </div>
                  </div>
                </Alert>
              )}
            </div>
          ) : (
            <div className="space-y-4 text-left">
              <Alert variant="success">
                <div className="font-medium text-lg">Quiz Completed!</div>
                <div className="text-sm">Your style profile has been saved.</div>
              </Alert>
            </div>
          )}
          
          <div className="mt-8 space-y-3">
            {countdown && (
              <div className="text-sm text-neutral-600 text-center mb-4">
                Redirecting to recommendations in {countdown} seconds...
              </div>
            )}
            <Button 
              onClick={() => navigate('/recommendations')}
              className="w-full"
              size="lg"
            >
              Get AI Recommendations
            </Button>
            <Button 
              variant="outline"
              onClick={() => navigate('/closet')}
              className="w-full"
            >
              View My Closet
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                setCurrentStep('gender')
                setCurrentCategory(0)
                setSelections({})
                setResult(null)
              }}
              className="w-full"
            >
              Retake Quiz
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={layoutClasses.pageContainer}>
      <div className="max-w-2xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Question {currentCategory + 1} of {CATEGORIES.length}</span>
            <span className="text-sm text-neutral-600">{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div 
              className="bg-neutral-900 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question */}
        <div className="text-center mb-8">
          <h1 className="text-xl font-bold mb-2">
            Which {CATEGORY_LABELS[currentCategoryName as keyof typeof CATEGORY_LABELS]} do you prefer?
          </h1>
          <p className="text-neutral-600">Choose the style that resonates with you most</p>
        </div>

        {/* Items */}
        {currentItems.length > 0 ? (
          <div className="grid grid-cols-2 gap-6 mb-8">
            {currentItems.map((item) => (
              <div
                key={item.id}
                className={`
                  border-2 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md
                  ${selectedItemId === item.id 
                    ? 'border-neutral-900 bg-neutral-50' 
                    : 'border-neutral-200 hover:border-neutral-300'
                  }
                `}
                onClick={() => handleItemSelect(currentCategoryName, item.id)}
              >
                <div className="aspect-square bg-neutral-100 rounded-lg mb-3 overflow-hidden">
                  <img 
                    src={item.image_url} 
                    alt={item.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = `https://via.placeholder.com/200x200.png?text=${encodeURIComponent(item.name)}`
                    }}
                  />
                </div>
                <h3 className="font-medium text-center">{item.name}</h3>
                {item.features.length > 0 && (
                  <div className="text-xs text-neutral-600 text-center mt-1">
                    {item.features.slice(0, 2).join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-neutral-400 mb-4">No items available for this category</div>
            <Button onClick={handleNext} disabled={loading}>
              Skip this question
            </Button>
          </div>
        )}

        <ErrorMessage error={error} className="mb-4" />

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentCategory === 0 || loading}
          >
            Previous
          </Button>
          
          <Button
            onClick={handleNext}
            disabled={loading || (currentItems.length > 0 && !selectedItemId)}
          >
            {loading ? 'Processing...' : currentCategory === CATEGORIES.length - 1 ? 'Complete Quiz' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  )
}
