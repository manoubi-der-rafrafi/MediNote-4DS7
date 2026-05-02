import { useOrchestrator } from './useOrchestrator';

export function useDelegateData(visitId: number = 541) {
  const { data, loading, error, refetch } = useOrchestrator(visitId, 'delegate');
  return {
    scorecard:    data?.data?.performance || data?.data?.delegate_scorecard || null,
    predictions:  data?.data?.predictions || null,
    coaching:     data?.data?.coaching || null,
    nlp:          data?.data?.nlp || null,
    riskScore:    data?.data?.risk_synthesis?.overall_risk_score ?? null,
    loading, error, refetch,
  };
}
