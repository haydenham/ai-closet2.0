import { layoutClasses } from '../utils/layout'
import { Button } from '../components/ui'
import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className={layoutClasses.pageContainer}>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight mb-3">Welcome to Nomi</h1>
        <p className="text-neutral-600 leading-relaxed mb-8">
          Your AI-powered style assistant. Nomi analyzes your wardrobe and creates personalized outfit recommendations for any occasion.
        </p>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div className={layoutClasses.card}>
            <h3 className="font-medium mb-2">📱 Build Your Digital Closet</h3>
            <p className="text-sm text-neutral-600 mb-4">Upload photos of your clothes and let Nomi organize your wardrobe.</p>
            <Link to="/closet">
              <Button variant="outline" size="sm">View My Closet</Button>
            </Link>
          </div>
          
          <div className={layoutClasses.card}>
            <h3 className="font-medium mb-2">✨ Get Outfit Ideas</h3>
            <p className="text-sm text-neutral-600 mb-4">Tell Nomi your plans and get AI-curated outfit recommendations.</p>
            <Link to="/recommendations">
              <Button size="sm">Get Recommendations</Button>
            </Link>
          </div>
        </div>
        
        <div className="text-sm text-neutral-500">
          New to Nomi? Start by <Link to="/closet/add" className="text-neutral-900 underline">adding some items</Link> to your closet, then get your first AI recommendation!
        </div>
      </div>
    </div>
  )
}
