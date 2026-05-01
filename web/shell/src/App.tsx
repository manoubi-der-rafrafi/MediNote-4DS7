import React, { useEffect, useState } from 'react';
import { useAuth } from './lib/auth';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BarChart3, TrendingUp, Target, AlertTriangle } from 'lucide-react';

const queryClient = new QueryClient();

// Mock Dashboard Component
const MockDashboard: React.FC<{ role: string }> = ({ role }) => {
  const roleInfo = {
    manager: {
      title: 'Manager Dashboard',
      icon: TrendingUp,
      kpis: [
        { label: 'CA Total', value: '3.81M', unit: 'MAD', color: 'bg-purple-500' },
        { label: 'Visites', value: '825', color: 'bg-blue-500' },
        { label: 'Rx', value: '281', color: 'bg-green-500' },
        { label: 'Score', value: '78', color: 'bg-yellow-500' },
      ],
    },
    marketing: {
      title: 'Marketing Dashboard',
      icon: Target,
      kpis: [
        { label: 'Segments', value: '4', color: 'bg-orange-500' },
        { label: 'Sentiment', value: '74%', color: 'bg-blue-500' },
        { label: 'ROI', value: '+28%', color: 'bg-green-500' },
        { label: 'Animations', value: '892', color: 'bg-pink-500' },
      ],
    },
    direction: {
      title: 'Direction Dashboard',
      icon: BarChart3,
      kpis: [
        { label: 'KPIs', value: '6', color: 'bg-red-500' },
        { label: 'Régions', value: '5', color: 'bg-blue-500' },
        { label: 'Croissance', value: '+19%', color: 'bg-green-500' },
        { label: 'Alertes', value: '3', color: 'bg-yellow-500' },
      ],
    },
  };

  const info = roleInfo[role as keyof typeof roleInfo] || roleInfo.manager;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">{info.title}</h1>
        <p className="text-gray-400">Welcome to CRM Pharma</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {info.kpis.map((kpi, i) => (
          <div key={i} className="bg-s1 border border-bd rounded-lg p-6">
            <p className="text-gray-400 text-sm mb-2">{kpi.label}</p>
            <p className="text-3xl font-bold text-white mb-2">{kpi.value}</p>
            <div className={`${kpi.color} h-1 rounded-full`}></div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-s1 border border-bd rounded-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Features</h2>
        <ul className="text-gray-300 space-y-2">
          <li>✓ Real-time KPI tracking</li>
          <li>✓ Team performance monitoring</li>
          <li>✓ Market analysis & predictions</li>
          <li>✓ Strategic alerts & notifications</li>
        </ul>
      </div>
    </div>
  );
};

function App() {
  const { token } = useAuth();
  const [active, setActive] = useState<'manager' | 'marketing' | 'direction'>('manager');

  useEffect(() => {
    const saved = localStorage.getItem('active_dashboard') as any;
    if (saved) setActive(saved);
  }, []);

  const handleNavigate = (role: string) => {
    setActive(role as any);
    localStorage.setItem('active_dashboard', role);
  };

  if (!token) {
    return <LoginPage />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AppLayout role={active} onNavigate={handleNavigate}>
        <MockDashboard role={active} />
      </AppLayout>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#22222A',
            color: '#F4F4F6',
            border: '1px solid rgba(255,255,255,0.08)',
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
