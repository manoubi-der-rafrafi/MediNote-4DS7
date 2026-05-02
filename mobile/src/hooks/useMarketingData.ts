import { useOrchestrator } from './useOrchestrator';

export function useMarketingData(visitId: number = 541) {
  const { data, loading, error } = useOrchestrator(visitId, 'marketing');
  const marketing = data?.data || {};

  return {
    data,
    loading,
    error,
    animations: marketing?.animations || [],
    budgetROI: marketing?.budget_roi || {},
    sentimentAnalysis: marketing?.sentiment || {},
    themes: marketing?.themes || [],
    roiAnalysis: marketing?.roi || {},
    nlpInsights: marketing?.nlp || {},
  };
}
