import { useOrchestrator } from './useOrchestrator';

export function useSupervisorData(visitId: number = 123) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'supervisor');
  return {
    delegates:    data?.data?.delegates || [],
    performance:  data?.data?.performance || null,
    riskSynthesis: data?.data?.risk_synthesis || null,
    coaching:     data?.data?.coaching || [],
    loading, error, refetch,
  };
}
