import React from 'react';
import { useAuth } from '../lib/auth';
import { LogOut, LayoutDashboard } from 'lucide-react';
import ChatWidget from './ChatWidget';

interface AppLayoutProps {
  role?: string;
  children: React.ReactNode;
  onNavigate: (path: string) => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ role = 'manager', children, onNavigate }) => {
  const { user, logout } = useAuth();

  const roleColors = {
    manager: 'bg-manager',
    marketing: 'bg-marketing',
    direction: 'bg-direction',
  };

  const roleColor = roleColors[role as keyof typeof roleColors] || 'bg-blue';

  return (
    <div className="flex h-screen bg-bg">
      {/* Sidebar */}
      <div className="w-64 bg-s1 border-r border-bd flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-bd">
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-8 h-8 ${roleColor} rounded-lg flex items-center justify-center`}>
              <LayoutDashboard className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white">CRM Pharma</h1>
              <p className="text-xs text-gray-400 capitalize">{role}</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="px-6 py-4 border-b border-bd">
          <p className="text-xs text-gray-400 mb-1">Logged in as</p>
          <p className="text-sm font-semibold text-white truncate">{user?.email}</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <p className="text-xs font-semibold text-gray-400 mb-3 uppercase">App Switcher</p>
          <div className="space-y-2">
            <button
              onClick={() => onNavigate('manager')}
              className={`w-full text-left px-4 py-2 rounded-lg font-medium transition-colors ${
                role === 'manager'
                  ? 'bg-manager text-white'
                  : 'text-gray-300 hover:bg-s2'
              }`}
            >
              Manager
            </button>
            <button
              onClick={() => onNavigate('marketing')}
              className={`w-full text-left px-4 py-2 rounded-lg font-medium transition-colors ${
                role === 'marketing'
                  ? 'bg-marketing text-white'
                  : 'text-gray-300 hover:bg-s2'
              }`}
            >
              Marketing
            </button>
            <button
              onClick={() => onNavigate('direction')}
              className={`w-full text-left px-4 py-2 rounded-lg font-medium transition-colors ${
                role === 'direction'
                  ? 'bg-direction text-white'
                  : 'text-gray-300 hover:bg-s2'
              }`}
            >
              Direction
            </button>
          </div>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-bd">
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-s2 hover:bg-s3 rounded-lg text-gray-300 hover:text-white transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
      <ChatWidget role={role} />
    </div>
  );
};
