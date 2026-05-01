import axios, { AxiosError, AxiosInstance } from 'axios';

/**
 * Unified API Service for Pharma CRM Frontend
 * Connects all 3 roles (Manager, Direction, Marketing) to Python Flask backend
 * 
 * Features:
 * - Automatic retry on 5xx errors
 * - JWT token management
 * - Request/response interceptors
 * - Type-safe API calls
 * - Mock data fallback for development
 */

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp?: string;
}

export interface ApiError {
  status: number;
  message: string;
  endpoint: string;
  timestamp: string;
}

// Create axios instance for FastAPI backend (no /api prefix)
export const createApiClient = (baseURL = 'http://localhost:8000'): AxiosInstance => {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: add JWT token
  client.interceptors.request.use(
    config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    error => Promise.reject(error)
  );

  // Response interceptor: handle errors + retry
  client.interceptors.response.use(
    response => response,
    async (error: AxiosError) => {
      const config = error.config as any;
      
      // Retry logic for 5xx errors (max 3 retries)
      if (error.response?.status && error.response.status >= 500) {
        config.retryCount = config.retryCount || 0;
        if (config.retryCount < 3) {
          config.retryCount += 1;
          console.warn(`🔄 Retrying request (attempt ${config.retryCount}/3)...`);
          await new Promise(resolve => setTimeout(resolve, 1000 * config.retryCount));
          return client(config);
        }
      }

      // Handle 401: clear token and redirect to login
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }
  );

  return client;
};

export const apiClient = createApiClient();

/**
 * MANAGER ROLE - API Functions
 */
export const managerAPI = {
  /**
   * Get dashboard overview with delegate performance
   * GET /api/commercial
   */
  getDashboard: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/commercial');
      return res.data?.data || res.data;
    } catch (err) {
      console.error('Failed to fetch manager dashboard:', err);
      throw err;
    }
  },

  /**
   * Get all delegates with performance scores
   * GET /api/commercial?filter=all
   */
  getDelegates: async (filter?: string): Promise<any> => {
    try {
      const params = filter ? { filter } : {};
      const res = await apiClient.get('/commercial', { params });
      return res.data?.data?.delegates || [];
    } catch (err) {
      console.error('Failed to fetch delegates:', err);
      throw err;
    }
  },

  /**
   * Get anomalies for the last 30 days
   * GET /api/it-health
   */
  getAnomalies: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/it-health');
      return res.data?.data?.anomalies || [];
    } catch (err) {
      console.error('Failed to fetch anomalies:', err);
      throw err;
    }
  },

  /**
   * Get forecast for multiple products
   * GET /api/finance?mode=forecast
   */
  getForecast: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/finance', { params: { mode: 'forecast' } });
      return res.data?.data?.forecast || [];
    } catch (err) {
      console.error('Failed to fetch forecast:', err);
      throw err;
    }
  },

  /**
   * Get coaching plan for specific delegate
   * GET /api/hr?delegate_id=<id>
   */
  getCoachingPlan: async (delegateId: number): Promise<any> => {
    try {
      const res = await apiClient.get('/hr', { params: { delegate_id: delegateId } });
      return res.data?.data?.coaching_plan || null;
    } catch (err) {
      console.error(`Failed to fetch coaching plan for delegate ${delegateId}:`, err);
      throw err;
    }
  },
};

/**
 * DIRECTION ROLE - API Functions
 */
export const directionAPI = {
  /**
   * Get executive KPIs dashboard
   * GET /api/direction
   */
  getKPIs: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/direction');
      return res.data?.data || res.data;
    } catch (err) {
      console.error('Failed to fetch KPIs:', err);
      throw err;
    }
  },

  /**
   * Get 3-month revenue forecast
   * GET /api/direction?mode=forecast
   */
  getForecast: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/direction', { params: { mode: 'forecast' } });
      return res.data?.data?.forecast || [];
    } catch (err) {
      console.error('Failed to fetch forecast:', err);
      throw err;
    }
  },

  /**
   * Get geographic performance data
   * GET /api/direction?mode=geography
   */
  getGeography: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/direction', { params: { mode: 'geography' } });
      return res.data?.data?.geography || [];
    } catch (err) {
      console.error('Failed to fetch geography:', err);
      throw err;
    }
  },

  /**
   * Get strategic alerts
   * GET /api/direction?mode=alerts
   */
  getAlerts: async (level?: 'CRITICAL' | 'URGENT' | 'WATCH'): Promise<any> => {
    try {
      const params = level ? { level } : {};
      const res = await apiClient.get('/direction', { params: { mode: 'alerts', ...params } });
      return res.data?.data?.alerts || [];
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      throw err;
    }
  },

  /**
   * Get financial forecast data
   * GET /api/finance
   */
  getFinance: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/finance');
      return res.data?.data || res.data;
    } catch (err) {
      console.error('Failed to fetch financial data:', err);
      throw err;
    }
  },
};

/**
 * MARKETING ROLE - API Functions
 */
export const marketingAPI = {
  /**
   * Get doctor/pharmacy segmentation
   * GET /api/medical?mode=segments
   */
  getSegments: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/medical', { params: { mode: 'segments' } });
      return res.data?.data?.segments || [];
    } catch (err) {
      console.error('Failed to fetch segments:', err);
      throw err;
    }
  },

  /**
   * Get sentiment analysis for comments
   * GET /api/nlp (or medical endpoint)
   */
  getSentiment: async (): Promise<any> => {
    try {
      // Try NLP endpoint first, fallback to medical
      try {
        const res = await apiClient.get('/nlp');
        return res.data?.data || res.data;
      } catch {
        const res = await apiClient.get('/medical', { params: { mode: 'sentiment' } });
        return res.data?.data?.sentiment || [];
      }
    } catch (err) {
      console.error('Failed to fetch sentiment:', err);
      throw err;
    }
  },

  /**
   * Get animation ROI analysis
   * GET /api/marketing or /api/roi
   */
  getROI: async (): Promise<any> => {
    try {
      // Try marketing endpoint first
      try {
        const res = await apiClient.get('/marketing');
        return res.data?.data || res.data;
      } catch {
        // Fallback to ROI endpoint if available
        const res = await apiClient.get('/roi');
        return res.data?.data || res.data;
      }
    } catch (err) {
      console.error('Failed to fetch ROI:', err);
      throw err;
    }
  },

  /**
   * Get comment details with flags
   * GET /api/medical?report_id=<id>
   */
  getCommentDetails: async (reportId: number): Promise<any> => {
    try {
      const res = await apiClient.get('/medical', { params: { report_id: reportId } });
      return res.data?.data || null;
    } catch (err) {
      console.error(`Failed to fetch comment ${reportId}:`, err);
      throw err;
    }
  },
};

/**
 * SHARED - Common API Functions
 */
export const commonAPI = {
  /**
   * Get current user info
   * GET /api/user/current
   */
  getCurrentUser: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/user/current');
      return res.data?.data || null;
    } catch (err) {
      console.error('Failed to fetch current user:', err);
      return null;
    }
  },

  /**
   * Login with email/password
   * POST /api/user/login (custom endpoint if needed)
   */
  login: async (email: string, password: string): Promise<{ token: string; user: any }> => {
    try {
      const res = await apiClient.post('/user/login', { email, password });
      return res.data?.data || res.data;
    } catch (err) {
      console.error('Login failed:', err);
      throw err;
    }
  },

  /**
   * Logout
   * POST /api/user/logout
   */
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/user/logout');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  },

  /**
   * Get API health status
   * GET /api/status
   */
  getStatus: async (): Promise<any> => {
    try {
      const res = await apiClient.get('/status');
      return res.data?.data || null;
    } catch (err) {
      console.error('Failed to fetch API status:', err);
      return null;
    }
  },
};

/**
 * Helper function to determine which role API to use
 */
export const getRoleAPI = (role: 'manager' | 'direction' | 'marketing') => {
  switch (role) {
    case 'manager':
      return managerAPI;
    case 'direction':
      return directionAPI;
    case 'marketing':
      return marketingAPI;
    default:
      return commonAPI;
  }
};

/**
 * Error handler for API calls
 */
export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    return {
      status: error.response?.status || 500,
      message: error.response?.data?.error || error.message || 'Unknown error',
      endpoint: error.config?.url || 'unknown',
      timestamp: new Date().toISOString(),
    };
  }

  return {
    status: 500,
    message: error instanceof Error ? error.message : 'Unknown error',
    endpoint: 'unknown',
    timestamp: new Date().toISOString(),
  };
};

export default apiClient;
