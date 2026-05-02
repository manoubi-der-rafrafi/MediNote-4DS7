import { useState, useEffect, useRef } from 'react';
import { fetchAllRoles } from '../api/client';

const cache = new Map<string, { data: any; ts: number }>();
const CACHE_TTL = 30 * 60 * 1000;

export function useOrchestrator(visitId: number = 123, role: string = 'delegate') {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cacheKey = `${role}:${visitId}`;

  const fetchData = async () => {
    setLoading(true);
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.ts < CACHE_TTL) {
      setData(cached.data);
      setLoading(false);
      return;
    }
    try {
      const raw = await fetchAllRoles(visitId, role);
      const roleData = raw?.roles?.[role] || {};
      const result = {
        visit_id: raw.visit_id,
        timestamp: raw.timestamp,
        execution_time_sec: raw.execution_time_sec,
        data: roleData,
      };
      cache.set(cacheKey, { data: result, ts: Date.now() });
      setData(result);
      setError(null);
    } catch (e: any) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [visitId, role]);

  return { data, loading, error, refetch: fetchData };
}
