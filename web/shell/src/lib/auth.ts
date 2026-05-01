import { create } from 'zustand';
import { apiClient } from './api';

interface User {
  id: string;
  email: string;
  role: 'manager' | 'marketing' | 'direction';
}

interface AuthState {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// Mock users for demo
const mockUsers: { [key: string]: User } = {
  'manager@crmpharm.com': { id: '1', email: 'manager@crmpharm.com', role: 'manager' },
  'marketing@crmpharm.com': { id: '2', email: 'marketing@crmpharm.com', role: 'marketing' },
  'direction@crmpharm.com': { id: '3', email: 'direction@crmpharm.com', role: 'direction' },
};

export const useAuth = create<AuthState>(set => ({
  token: localStorage.getItem('auth_token'),
  user: localStorage.getItem('auth_user') ? JSON.parse(localStorage.getItem('auth_user')!) : null,

  login: async (email: string, password: string) => {
    try {
      // Mock login - no backend required
      if (mockUsers[email] && password === 'password') {
        const user = mockUsers[email];
        const token = 'mock_token_' + Date.now();

        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify(user));

        set({ token, user });
        return;
      }

      throw new Error('Invalid credentials');
    } catch (error: any) {
      throw new Error(error.message || 'Login failed');
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    set({ token: null, user: null });
    window.location.href = '/login';
  },
}));
