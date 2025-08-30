// Standardized spacing and layout utilities
// Use these consistent patterns throughout the application

export const layoutClasses = {
  // Page containers - consistent max-width and padding
  pageContainer: 'space-y-6',
  
  // Form layouts - consistent spacing between form elements
  form: 'space-y-4',
  formField: 'space-y-2',
  
  // Content sections - consistent vertical spacing
  section: 'space-y-4',
  sectionLarge: 'space-y-6',
  
  // Lists and grids - consistent gaps
  listVertical: 'space-y-3',
  listVerticalLarge: 'space-y-6',
  gridResponsive: 'grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
  
  // Inline elements - consistent horizontal spacing
  inlineGroup: 'flex items-center gap-2',
  inlineGroupLarge: 'flex items-center gap-4',
  
  // Cards and content blocks - consistent padding
  card: 'border border-neutral-200 rounded-sm p-4 bg-white',
  cardSmall: 'border border-neutral-200 rounded-sm p-3',
  
  // Status and metadata - consistent styling
  metadata: 'text-xs text-neutral-600 flex gap-2 flex-wrap',
  
  // Tags and badges - consistent styling
  badge: 'px-1.5 py-0.5 bg-neutral-100 text-neutral-700 rounded-sm text-xs tracking-wide',
  badgeSmall: 'px-1.5 py-0.5 bg-neutral-100 text-neutral-700 rounded-sm text-[10px] tracking-wide uppercase'
} as const

// Container component for consistent page layout
export const pageContainerClasses = 'space-y-6'
export const formContainerClasses = 'space-y-4 max-w-xl'
export const sectionContainerClasses = 'space-y-4'
