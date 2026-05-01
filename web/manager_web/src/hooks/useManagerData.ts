import { useOrchestrator } from '../../../shared/src/hooks/useOrchestrator';

/**
 * Hook for supervisor role - returns manager/supervisor specific data
 */
export function useManagerData(visitId: number = 123) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'supervisor');

  return {
    // Full orchestrator response
    orchestratorResponse: data,
    
    // Supervisor-specific data
    supervisorData: data?.data,
    
    // Extracted fields for common views
    delegates: data?.data?.delegates || [],
    delegateScores: data?.data?.delegate_scores || [],
    delegateCoaching: data?.data?.coaching || [],
    delegateAnomalies: data?.data?.anomalies || [],
    forecastData: data?.data?.forecast || {},
    performanceMetrics: data?.data?.performance || {},
    riskSynthesis: data?.data?.risk_synthesis || {},
    
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

export type ManagerData = ReturnType<typeof useManagerData>;
