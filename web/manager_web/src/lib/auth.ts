import { create } from 'zustand';

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'manager' | 'marketing' | 'direction' | 'admin';
}

export interface AuthStore {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

// Mock users for development
const MOCK_USERS: Record<string, { user: User; password: string }> = {
  'laurent@pharma.com': {
    password: 'Laurent2024!',
    user: {
      id: 1,
      name: 'Laurent Manager',
      email: 'laurent@pharma.com',
      role: 'manager',
    },
  },
  'sophie@pharma.com': {
    password: 'Sophie2024!',
    user: {
      id: 3,
      name: 'Sophie Marketing',
      email: 'sophie@pharma.com',
      role: 'marketing',
    },
  },
  'pierre@pharma.com': {
    password: 'Pierre2024!',
    user: {
      id: 2,
      name: 'Pierre Direction',
      email: 'pierre@pharma.com',
      role: 'direction',
    },
  },
  // Legacy test credentials
  'manager@crmpharm.com': {
    password: 'password',
    user: {
      id: 1,
      name: 'Laurent Manager',
      email: 'manager@crmpharm.com',
      role: 'manager',
    },
  },
  'director@crmpharm.com': {
    password: 'password',
    user: {
      id: 2,
      name: 'Pierre Director',
      email: 'director@crmpharm.com',
      role: 'direction',
    },
  },
  'marketing@crmpharm.com': {
    password: 'password',
    user: {
      id: 3,
      name: 'Sophie Marketing',
      email: 'marketing@crmpharm.com',
      role: 'marketing',
    },
  },
};

export const useAuth = create<AuthStore>(set => ({
  token: localStorage.getItem('token'),
  user: (() => {
    try {
      return JSON.parse(localStorage.getItem('user') || 'null') as User | null;
    } catch {
      return null;
    }
  })(),
  isLoading: false,
  
  login: async (email: string, password: string) => {
    set({ isLoading: true });
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    try {
      const mockUser = MOCK_USERS[email];
      if (!mockUser || mockUser.password !== password) {
        throw new Error('Identifiants invalides');
      }
      
      const token = `mock_token_${Date.now()}`;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(mockUser.user));
      set({
        token,
        user: mockUser.user,
        isLoading: false,
      });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.clear();
    set({ token: null, user: null });
    window.location.href = '/login';
  },

  setUser: (user: User) => {
    localStorage.setItem('user', JSON.stringify(user));
    set({ user });
  },
}));
