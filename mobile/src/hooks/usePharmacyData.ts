import { useOrchestrator } from './useOrchestrator';

export function usePharmacyData(visitId: number = 123) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'pharmacy');
  return {
    operations:  data?.data?.operations || null,
    demand:      data?.data?.demand || null,
    financial:   data?.data?.financial || null,
    risk:        data?.data?.risk || null,
    feedback:    data?.data?.feedback || null,
    performance: data?.data?.performance || null,
    loading, error, refetch,
  };
}
