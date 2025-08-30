import { layoutClasses } from '../utils/layout'

export function HomePage() {
  return (
    <div className={layoutClasses.pageContainer}>
      <h1 className="text-xl font-semibold tracking-tight">Welcome to Nomi</h1>
      <p className="text-sm leading-relaxed max-w-prose text-neutral-600">
        Your AI-powered style assistant. Nomi helps you extract visual features from clothing images, track satisfaction signals, and get personalized outfit recommendations. Start by navigating to the Feature Extraction section to begin building your digital closet.
      </p>
    </div>
  )
}
