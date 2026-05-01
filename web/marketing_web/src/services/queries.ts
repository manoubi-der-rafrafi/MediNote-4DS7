import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import {
  managerAPI,
  directionAPI,
  marketingAPI,
  commonAPI,
  handleApiError,
} from './api';

/**
 * React Query Hooks for Pharma CRM
 * Centralized server state management with caching, retry, and error handling
 */

// ═════════════════════════════════════════════════════════════════════════════
// MANAGER ROLE HOOKS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch manager dashboard data
 * Auto-refetches every 30 seconds (active polling)
 */
export const useManagerDashboard = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['manager', 'dashboard'],
    queryFn: () => managerAPI.getDashboard(),
    staleTime: 1000 * 30, // 30 seconds
    gcTime: 1000 * 60 * 5, // 5 minutes (formerly cacheTime)
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Fetch all delegates list
 */
export const useManagerDelegates = (filter?: string): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['manager', 'delegates', filter],
    queryFn: () => managerAPI.getDelegates(filter),
    staleTime: 1000 * 60, // 1 minute
    gcTime: 1000 * 60 * 10, // 10 minutes
    retry: 2,
  });
};

/**
 * Fetch anomalies
 */
export const useManagerAnomalies = (): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['manager', 'anomalies'],
    queryFn: () => managerAPI.getAnomalies(),
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 10,
    retry: 2,
  });
};

/**
 * Fetch forecast data
 */
export const useManagerForecast = (): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['manager', 'forecast'],
    queryFn: () => managerAPI.getForecast(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30,
    retry: 1,
  });
};

/**
 * Fetch coaching plan for a delegate
 */
export const useManagerCoachingPlan = (delegateId: number): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['manager', 'coaching', delegateId],
    queryFn: () => managerAPI.getCoachingPlan(delegateId),
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 30,
    retry: 1,
  });
};

// ═════════════════════════════════════════════════════════════════════════════
// DIRECTION ROLE HOOKS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch executive KPIs
 */
export const useDirectionKPIs = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['direction', 'kpis'],
    queryFn: () => directionAPI.getKPIs(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
};

/**
 * Fetch forecast for Direction
 */
export const useDirectionForecast = (): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['direction', 'forecast'],
    queryFn: () => directionAPI.getForecast(),
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 30,
    retry: 1,
  });
};

/**
 * Fetch geographic data
 */
export const useDirectionGeography = (): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['direction', 'geography'],
    queryFn: () => directionAPI.getGeography(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 1,
  });
};

/**
 * Fetch strategic alerts
 * @param level - Filter by CRITICAL, URGENT, or WATCH
 */
export const useDirectionAlerts = (
  level?: 'CRITICAL' | 'URGENT' | 'WATCH'
): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['direction', 'alerts', level],
    queryFn: () => directionAPI.getAlerts(level),
    staleTime: 1000 * 60 * 2, // 2 minutes (alerts should be fresher)
    gcTime: 1000 * 60 * 15,
    retry: 2,
  });
};

/**
 * Fetch financial data
 */
export const useDirectionFinance = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['direction', 'finance'],
    queryFn: () => directionAPI.getFinance(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
};

// ═════════════════════════════════════════════════════════════════════════════
// MARKETING ROLE HOOKS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch segmentation data (doctors + pharmacies)
 */
export const useMarketingSegments = (): UseQueryResult<any[], unknown> => {
  return useQuery({
    queryKey: ['marketing', 'segments'],
    queryFn: () => marketingAPI.getSegments(),
    staleTime: 1000 * 60 * 15, // 15 minutes (clustering is stable)
    gcTime: 1000 * 60 * 60,
    retry: 1,
  });
};

/**
 * Fetch sentiment analysis data
 */
export const useMarketingSentiment = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['marketing', 'sentiment'],
    queryFn: () => marketingAPI.getSentiment(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
};

/**
 * Fetch ROI analysis
 */
export const useMarketingROI = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['marketing', 'roi'],
    queryFn: () => marketingAPI.getROI(),
    staleTime: 1000 * 60 * 15,
    gcTime: 1000 * 60 * 60,
    retry: 1,
  });
};

/**
 * Fetch comment details
 */
export const useMarketingCommentDetails = (reportId: number): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['marketing', 'comment', reportId],
    queryFn: () => marketingAPI.getCommentDetails(reportId),
    staleTime: 1000 * 60 * 30, // 30 minutes (comments are historical)
    gcTime: 1000 * 60 * 60,
    retry: 1,
    enabled: reportId > 0, // Only fetch if reportId is valid
  });
};

// ═════════════════════════════════════════════════════════════════════════════
// COMMON HOOKS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch current user
 */
export const useCurrentUser = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['user', 'current'],
    queryFn: () => commonAPI.getCurrentUser(),
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 24, // 24 hours
    retry: 1,
  });
};

/**
 * Check API health status
 */
export const useApiStatus = (): UseQueryResult<any, unknown> => {
  return useQuery({
    queryKey: ['api', 'status'],
    queryFn: () => commonAPI.getStatus(),
    staleTime: 1000 * 30, // 30 seconds
    gcTime: 1000 * 60 * 5,
    retry: 2,
  });
};

// ═════════════════════════════════════════════════════════════════════════════
// MUTATION HOOKS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Login mutation
 */
export const useLogin = (): UseMutationResult<
  { token: string; user: any },
  unknown,
  { email: string; password: string }
> => {
  return useMutation({
    mutationFn: async ({ email, password }) => {
      return commonAPI.login(email, password);
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
    },
    onError: (error) => {
      console.error('Login failed:', handleApiError(error));
    },
  });
};

/**
 * Logout mutation
 */
export const useLogout = (): UseMutationResult<void, unknown, void> => {
  return useMutation({
    mutationFn: async () => {
      return commonAPI.logout();
    },
  });
};

// ═════════════════════════════════════════════════════════════════════════════
// HELPER HOOK FOR LOADING/ERROR STATES
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Hook to combine multiple queries and get overall loading/error state
 */
export const useMultipleQueries = (queries: UseQueryResult<any, unknown>[]) => {
  const isLoading = queries.some(q => q.isLoading);
  const isError = queries.some(q => q.isError);
  const error = queries.find(q => q.error)?.error;

  return { isLoading, isError, error };
};

export default {
  // Manager
  useManagerDashboard,
  useManagerDelegates,
  useManagerAnomalies,
  useManagerForecast,
  useManagerCoachingPlan,

  // Direction
  useDirectionKPIs,
  useDirectionForecast,
  useDirectionGeography,
  useDirectionAlerts,
  useDirectionFinance,

  // Marketing
  useMarketingSegments,
  useMarketingSentiment,
  useMarketingROI,
  useMarketingCommentDetails,

  // Common
  useCurrentUser,
  useApiStatus,
  useLogin,
  useLogout,
  useMultipleQueries,
};
