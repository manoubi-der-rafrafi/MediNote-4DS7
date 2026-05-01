import React, { ReactNode } from 'react';
import { Sidebar } from '../ui/Sidebar';
import { User } from '../../lib/auth';
import {
  Target,
  MessageCircle,
  DollarSign,
} from 'lucide-react';

interface AppLayoutProps {
  children: ReactNode;
  user: User | null;
  onLogout: () => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, user, onLogout }) => {
  const menuItems = [
    {
      icon: Target,
      label: 'Segments',
      path: '/segments',
    },
    {
      icon: MessageCircle,
      label: 'Sentiment NLP',
      path: '/sentiment',
    },
    {
      icon: DollarSign,
      label: 'ROI Animations',
      path: '/roi',
    },
  ];

  return (
    <div className="flex h-screen bg-bg">
      <Sidebar
        items={menuItems}
        brandColor="orange"
        role={user?.role || 'marketing'}
        onLogout={onLogout}
      />

      <main className="ml-60 flex-1 overflow-auto">
        <div className="p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
};
