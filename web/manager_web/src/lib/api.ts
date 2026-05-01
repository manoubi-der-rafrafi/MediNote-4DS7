import axios from 'axios';

// API Client (FastAPI orchestrator on localhost:8000)
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
});

const API_KEY = import.meta.env.VITE_API_KEY || 'mgr-key-2026';

// Inject supervisor API key on every request
api.interceptors.request.use(config => {
  config.headers['X-API-Key'] = API_KEY;
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

// New orchestrator API functions
export const orchestratorAPI = {
  // Fetch predictions for a visit (all roles)
  getPredictionsAllRoles: async (visitId: number = 123) => {
    const res = await api.get(`/predictions/${visitId}/all-roles`);
    return res.data;
  },

  // Fetch predictions for a visit with specific role
  getPredictions: async (visitId: number = 123, role: string = 'supervisor') => {
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

// User/Auth API Functions
export const userAPI = {
  // Get current logged-in user
  getCurrentUser: async () => {
    try {
      const res = await api.get('/user/current');
      return res.data;
    } catch (err: any) {
      return null;
    }
  },

  // Get all doctors
  getDoctors: async () => {
    try {
      const res = await api.get('/doctors');
      return res.data;
    } catch (err: any) {
      throw err.response?.data || err.message;
    }
  },

  // Get all delegates
  getDelegates: async () => {
    try {
      const res = await api.get('/delegates');
      return res.data;
    } catch (err: any) {
      throw err.response?.data || err.message;
    }
  },

  // Get doctor by ID
  getDoctor: async (doctorId: number) => {
    try {
      const res = await api.get(`/doctors/${doctorId}`);
      return res.data;
    } catch (err: any) {
      throw err.response?.data || err.message;
    }
  },

  // Get delegate by ID
  getDelegate: async (delegateId: number) => {
    try {
      const res = await api.get(`/delegates/${delegateId}`);
      return res.data;
    } catch (err: any) {
      throw err.response?.data || err.message;
    }
  },
};
