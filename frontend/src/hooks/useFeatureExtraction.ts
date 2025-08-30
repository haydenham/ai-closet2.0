import { useMutation } from '@tanstack/react-query'
import { extractFeatures, FeatureExtractionRequest, FeatureExtractionResult } from '../api/featureLearning'

export function useFeatureExtraction() {
  return useMutation<FeatureExtractionResult[], Error, FeatureExtractionRequest>({
    mutationFn: extractFeatures
  })
}
