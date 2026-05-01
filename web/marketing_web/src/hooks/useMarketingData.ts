import { useOrchestrator } from '../../../shared/src/hooks/useOrchestrator';

/**
 * Hook for marketing role - returns marketing specific data
 */
export function useMarketingData(visitId: number = 123) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'marketing');

  return {
    // Full orchestrator response
    orchestratorResponse: data,
    
    // Marketing-specific data
    marketingData: data?.data,
    
    // Extracted fields for common views
    animations: data?.data?.animations || [],
    budgetROI: data?.data?.budget_roi || {},
    eligibilityData: data?.data?.eligibility || {},
    forecastData: data?.data?.forecast || {},
    sentimentAnalysis: data?.data?.sentiment || {},
    themes: data?.data?.themes || [],
    roiAnalysis: data?.data?.roi || {},
    nlpInsights: data?.data?.nlp || {},
    
    // Metadata
    visitId: data?.visit_id,
    executionTime: data?.execution_time_sec,
    fromCache: data?.from_cache,
    timestamp: data?.timestamp,
    
    // State
    loading,
    error,
    refetch,
  };
}

export type MarketingData = ReturnType<typeof useMarketingData>;
