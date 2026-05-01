import { useEffect, useState } from 'react';
import axios from 'axios';

const ORCHESTRATOR_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

interface CacheEntry {
  data: any;
  timestamp: number;
}

const cache = new Map<string, CacheEntry>();

export type OrchestratorRole = 'supervisor' | 'founder' | 'marketing' | 'pharmacy' | 'doctor' | 'delegate' | 'admin';

const roleApiKeys: Record<OrchestratorRole, string> = {
  supervisor: 'sup-key-2026',
  founder: 'fdr-key-2026',
  marketing: 'mkt-key-2026',
  pharmacy: 'ph-key-2026',
  doctor: 'dr-key-2026',
  delegate: 'dlg-key-2026',
  admin: 'admin-key-2026',
};

export interface UseOrchestratorReturn {
  data: any;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch orchestrator data for a visit with role-based filtering.
 * Caches results for 30 minutes.
 * 
 * @param visitId - Visit ID to fetch (default: 123 for dev)
 * @param role - Role to filter data by (default: 'supervisor')
 * @returns { data, loading, error, refetch }
 */
export function useOrchestrator(
  visitId: number = 123,
  role: OrchestratorRole = 'supervisor'
): UseOrchestratorReturn {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cacheKey = `orchestrator_${visitId}_${role}`;

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Check cache first
      const cached = cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        setData(cached.data);
        setLoading(false);
        return;
      }

      // Fetch all roles data
      const apiKey = roleApiKeys[role];
      if (!apiKey) {
        throw new Error(`Invalid role: ${role}`);
      }

      const response = await axios.get(`${ORCHESTRATOR_BASE_URL}/predictions/${visitId}/all-roles`, {
        headers: {
          'X-API-Key': apiKey,
        },
      });

      // Extract role-specific data
      const allRolesData = response.data.roles || {};
      const roleData = allRolesData[role] || {};

      const responseData = {
        visit_id: response.data.visit_id,
        timestamp: response.data.timestamp,
        execution_time_sec: response.data.execution_time_sec,
        from_cache: response.data.from_cache || false,
        data: roleData,
      };

      // Cache the result
      cache.set(cacheKey, {
        data: responseData,
        timestamp: Date.now(),
      });

      setData(responseData);
    } catch (err: any) {
      const error = new Error(
        err.response?.data?.detail || err.message || 'Failed to fetch orchestrator data'
      );
      setError(error);

      // If 401 or 403, redirect to login
      if (err.response?.status === 401 || err.response?.status === 403) {
        setTimeout(() => {
          window.location.href = '/login';
        }, 500);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [visitId, role]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}
