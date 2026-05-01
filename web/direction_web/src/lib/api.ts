import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API Client (FastAPI orchestrator)
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Inject founder API key on every request
api.interceptors.request.use(config => {
  config.headers['X-API-Key'] = 'fdr-key-2026';
  return config;
});

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 || err.response?.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// Orchestrator API functions
export const orchestratorAPI = {
  // Fetch predictions for a visit (all roles)
  getPredictionsAllRoles: async (visitId: number = 123) => {
    const res = await api.get(`/predictions/${visitId}/all-roles`);
    return res.data;
  },

  // Fetch predictions for a visit with specific role
  getPredictions: async (visitId: number = 123, role: string = 'founder') => {
    const res = await api.get(`/predictions/${visitId}`, {
      params: { role },
    });
    return res.data;
  },

  // Analyze a new visit
  analyzeVisit: async (visitData: Record<string, any>) => {
    const res = await api.post('/visits/analyze', visitData);
    return res.data;
  },

  // Get debug info for an agent
  getAgentDebug: async (agentName: string) => {
    const res = await api.get(`/debug/agent/${agentName}`);
    return res.data;
  },

  // Get performance metrics
  getPerformanceMetrics: async () => {
    const res = await api.get('/debug/performance');
    return res.data;
  },

  // Health check
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },
};

export default api;
