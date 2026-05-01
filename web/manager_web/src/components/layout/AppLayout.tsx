import React, { ReactNode } from 'react';
import { Sidebar } from '../ui/Sidebar';
import { User } from '../../lib/auth';
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';

interface AppLayoutProps {
  children: ReactNode;
  user: User | null;
  onLogout: () => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, user, onLogout }) => {
  const menuItems = [
    {
      icon: LayoutDashboard,
      label: 'Dashboard',
      path: '/dashboard',
    },
    {
      icon: Users,
      label: 'Mon équipe',
      path: '/team',
    },
    {
      icon: AlertTriangle,
      label: 'Anomalies',
      path: '/anomalies',
    },
    {
      icon: TrendingUp,
      label: 'Forecast',
      path: '/forecast',
    },
  ];

  return (
    <div className="flex h-screen bg-bg">
      <Sidebar
        items={menuItems}
        brandColor="purple"
        role={user?.role || 'manager'}
        onLogout={onLogout}
      />

      <main className="ml-60 flex-1 overflow-auto">
        <div className="p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
};
