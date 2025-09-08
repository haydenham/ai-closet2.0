// Category mapping for better user experience
export const CATEGORY_DISPLAY_NAMES = {
  'tops': 'Tops',
  'bottoms': 'Bottoms', 
  'dresses': 'Dresses',
  'outerwear': 'Outerwear',
  'shoes': 'Shoes',
  'accessories': 'Accessories',
  'underwear': 'Underwear',
  'activewear': 'Activewear',
  'formal': 'Outerwear & Layers', // Better name for formal category
  'casual': 'Casual'
} as const

export const CATEGORIES = Object.keys(CATEGORY_DISPLAY_NAMES) as Array<keyof typeof CATEGORY_DISPLAY_NAMES>

export const getCategoryDisplayName = (category: string): string => {
  return CATEGORY_DISPLAY_NAMES[category as keyof typeof CATEGORY_DISPLAY_NAMES] || category
}

// Reverse mapping for API calls
export const getBackendCategoryName = (displayName: string): string => {
  const entry = Object.entries(CATEGORY_DISPLAY_NAMES).find(([, display]) => display === displayName)
  return entry ? entry[0] : displayName.toLowerCase()
}
