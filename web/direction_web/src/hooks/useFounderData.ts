import { useOrchestrator } from '../../../shared/src/hooks/useOrchestrator';

/**
 * Hook for founder role - returns executive/founder specific data
 */
export function useFounderData(visitId: number = 123) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'founder');

  return {
    // Full orchestrator response
    orchestratorResponse: data,
    
    // Founder-specific data
    founderData: data?.data,
    
    // Extracted fields for common views
    kpis: data?.data?.kpis || {},
    executive: data?.data?.executive || {},
    revenue: data?.data?.revenue || {},
    market: data?.data?.market || {},
    supply: data?.data?.supply || {},
    people: data?.data?.people || {},
    animations: data?.data?.animations || [],
    forecasts: data?.data?.forecast || {},
    anomalies: data?.data?.anomalies || [],
    dataQuality: data?.data?.data_quality || {},
    riskSynthesis: data?.data?.risk_synthesis || {},
    alerts: data?.data?.alerte || {},
    compliance: data?.data?.compliance || {},
    finance: data?.data?.finance || {},
    
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

export type FounderData = ReturnType<typeof useFounderData>;
