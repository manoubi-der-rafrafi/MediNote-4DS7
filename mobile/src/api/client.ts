import { Platform } from 'react-native';

// PC local IP — phones on the same WiFi can reach this directly
const PC_IP = '192.168.1.11';

const getBaseUrl = () => {
  if (__DEV__) {
    if (Platform.OS === 'android') return `http://${PC_IP}:8000`;
    if (Platform.OS === 'ios')     return `http://${PC_IP}:8000`;
    return 'http://localhost:8000';
  }
  return `http://${PC_IP}:8000`;
};

export const BASE_URL = getBaseUrl();

export const API_KEYS: Record<string, string> = {
  delegate: 'del-key-2026',
  pharmacy: 'ph-key-2026',
  supervisor: 'sup-key-2026',
  marketing: 'mkt-key-2026',
  founder: 'fdr-key-2026',
};

export async function fetchAllRoles(visitId: number, role: string): Promise<any> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(`${BASE_URL}/predictions/${visitId}/all-roles`, {
      headers: { 'X-API-Key': API_KEYS[role] || API_KEYS.delegate },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export async function login(username: string, password: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function getDashboardKpis(token: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/dashboard/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function getMyPharmacies(token: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/my/pharmacies`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function getMyPerformance(token: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/my/performance`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function getAlerts(token: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/alerts`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
