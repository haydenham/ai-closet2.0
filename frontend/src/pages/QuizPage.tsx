import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { Alert, ErrorMessage } from '../components/ui/Alert'
import { QuizClothingItem, fetchQuizQuestions, submitQuiz, QuizSubmissionData } from '../api/quiz'
import { layoutClasses } from '../utils/layout'

// New quiz structure: 5 questions with 10 style options each
const QUESTION_TYPES = ['pants', 'shirt', 'shorts', 'overlayer', 'shoes']

export function QuizPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<'gender' | 'quiz' | 'results'>('gender')
  const [gender, setGender] = useState<'male' | 'female' | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [questions, setQuestions] = useState<Record<string, { text: string; items: QuizClothingItem[] }>>({})
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
      
      // Store questions with their text and items
      const questionsData: Record<string, { text: string; items: QuizClothingItem[] }> = {}
      QUESTION_TYPES.forEach(questionType => {
        const questionData = response.questions[questionType]
        if (questionData) {
          questionsData[questionType] = {
            text: questionData.question_text,
            items: questionData.items
          }
        }
      })
      
      setQuestions(questionsData)
      setCurrentStep('quiz')
    } catch (err: any) {
      setError(err.message || 'Failed to load quiz questions')
    } finally {
      setLoading(false)
    }
  }

  const handleItemSelect = (questionType: string, itemId: string) => {
    setSelections(prev => ({
      ...prev,
      [questionType]: itemId
    }))
  }

  const handleNext = () => {
    if (currentQuestionIndex < QUESTION_TYPES.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      handleSubmit()
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const handleSubmit = async () => {
    if (!gender) return
    
    setLoading(true)
    setError(null)
    
    try {
      const submission: QuizSubmissionData = {
        gender,
        selections: selections  // Backend expects "selections" key
      }
      
      console.log('Submitting quiz:', submission)
      const response = await submitQuiz(submission)
      console.log('Quiz response:', response)
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
      console.error('Quiz submission error:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  const currentQuestionType = QUESTION_TYPES[currentQuestionIndex]
  const currentQuestion = questions[currentQuestionType]
  const currentItems = currentQuestion?.items || []
  const currentQuestionText = currentQuestion?.text || ''
  const selectedItemId = selections[currentQuestionType]
  const progress = ((currentQuestionIndex + 1) / QUESTION_TYPES.length) * 100

  if (currentStep === 'gender') {
    return (
      <div className={layoutClasses.pageContainer}>
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-2xl font-bold mb-2">Style Quiz</h1>
          <p className="text-neutral-600 mb-8">
            Discover your personal style with our AI-powered quiz. Choose the items that resonate with you!
          </p>
          
          <div className="space-y-6">
            <h2 className="text-lg font-medium">Choose your style journey</h2>
            
            <div className="grid grid-cols-1 gap-6">
              <div
                className="border-2 border-neutral-200 rounded-lg p-6 cursor-pointer transition-all duration-200 hover:border-neutral-300 hover:shadow-md"
                onClick={() => handleGenderSelect('female')}
              >
                <div className="text-4xl mb-3">👗</div>
                <h3 className="font-semibold text-lg mb-2">Women's Style Quiz</h3>
                <p className="text-sm text-neutral-600">
                  Explore feminine fashion categories including dresses, blouses, accessories, and complete looks
                </p>
                <Button
                  variant="outline" 
                  size="sm"
                  disabled={loading}
                  className="mt-4"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleGenderSelect('female')
                  }}
                >
                  Start Women's Quiz
                </Button>
              </div>
              
              <div
                className="border-2 border-neutral-200 rounded-lg p-6 cursor-pointer transition-all duration-200 hover:border-neutral-300 hover:shadow-md"
                onClick={() => handleGenderSelect('male')}
              >
                <div className="text-4xl mb-3">👔</div>
                <h3 className="font-semibold text-lg mb-2">Men's Style Quiz</h3>
                <p className="text-sm text-neutral-600">
                  Discover masculine style preferences including suits, casual wear, accessories, and signature looks
                </p>
                <Button
                  variant="outline"
                  size="sm" 
                  disabled={loading}
                  className="mt-4"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleGenderSelect('male')
                  }}
                >
                  Start Men's Quiz
                </Button>
              </div>
            </div>
          </div>
          
          <ErrorMessage error={error} className="mt-6" />
          
          {loading && (
            <div className="mt-6 text-sm text-neutral-600">
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
                  <div className="font-medium text-2xl">
                    Your Style: {result.primary_style}
                  </div>
                  <div className="text-sm text-neutral-700">
                    {result.style_message}
                  </div>
                </div>
              </Alert>
              
              {result.secondary_style && (
                <Alert variant="info">
                  <div>
                    <div className="font-medium">Secondary Style</div>
                    <div className="text-sm">
                      {result.secondary_style}
                    </div>
                  </div>
                </Alert>
              )}
              
              {result.scores && Object.keys(result.scores).length > 0 && (
                <div className="bg-neutral-50 rounded-lg p-4">
                  <div className="font-medium mb-2">Your Style Breakdown</div>
                  <div className="space-y-1 text-sm">
                    {Object.entries(result.scores)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .map(([style, score]) => (
                        <div key={style} className="flex justify-between">
                          <span>{style}</span>
                          <span className="text-neutral-600">{score as number} {(score as number) === 1 ? 'point' : 'points'}</span>
                        </div>
                      ))}
                  </div>
                </div>
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
                setCurrentQuestionIndex(0)
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
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Question {currentQuestionIndex + 1} of {QUESTION_TYPES.length}</span>
            <span className="text-sm text-neutral-600">{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div 
              className="bg-neutral-900 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Text */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold mb-2">
            {currentQuestionText}
          </h1>
          <p className="text-neutral-600">Choose the style that resonates with you most</p>
        </div>

        {/* Items Grid - 10 images in a responsive grid */}
        {currentItems.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
            {currentItems.map((item) => (
              <div
                key={item.id}
                className={`
                  border-2 rounded-lg p-3 cursor-pointer transition-all duration-200 hover:shadow-lg
                  ${selectedItemId === item.id 
                    ? 'border-neutral-900 bg-neutral-50 shadow-md' 
                    : 'border-neutral-200 hover:border-neutral-400'
                  }
                `}
                onClick={() => handleItemSelect(currentQuestionType, item.id)}
              >
                <div className="aspect-[2/3] bg-neutral-100 rounded-lg mb-2 overflow-hidden">
                  <img 
                    src={item.image_url} 
                    alt={item.style_category}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = `https://via.placeholder.com/200x300.png?text=${encodeURIComponent(item.style_category)}`
                    }}
                  />
                </div>
                <h3 className="font-medium text-center text-sm capitalize">{item.style_category}</h3>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-neutral-400 mb-4">No items available for this question</div>
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
            disabled={currentQuestionIndex === 0 || loading}
          >
            Previous
          </Button>
          
          <Button
            onClick={handleNext}
            disabled={loading || (currentItems.length > 0 && !selectedItemId)}
          >
            {loading ? 'Processing...' : currentQuestionIndex === QUESTION_TYPES.length - 1 ? 'Complete Quiz' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  )
}
