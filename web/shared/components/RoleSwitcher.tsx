import React, { useState } from 'react';
import { User, ChevronDown, LogOut } from 'lucide-react';
import { User as UserType, useAuth } from '../lib/auth';

interface RoleSwitcherProps {
  user: UserType | null;
  onLogout: () => void;
}

const ROLE_CONFIGS: Record<string, { label: string; color: string; icon: string }> = {
  manager: {
    label: 'Manager',
    color: 'bg-blue-600',
    icon: '👔',
  },
  marketing: {
    label: 'Marketing',
    color: 'bg-purple-600',
    icon: '📊',
  },
  direction: {
    label: 'Direction',
    color: 'bg-red-600',
    icon: '🎯',
  },
  admin: {
    label: 'Admin',
    color: 'bg-green-600',
    icon: '⚙️',
  },
};

export const RoleSwitcher: React.FC<RoleSwitcherProps> = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const roleConfig = ROLE_CONFIGS[user?.role || 'admin'];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
      >
        <div className={`${roleConfig.color} p-2 rounded text-white text-sm`}>
          {roleConfig.icon}
        </div>
        <div className="text-left">
          <p className="text-sm font-semibold text-white">{user?.name}</p>
          <p className="text-xs text-gray-400">{roleConfig.label}</p>
        </div>
        <ChevronDown
          size={18}
          className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50">
          {/* User Info */}
          <div className="p-4 border-b border-gray-700">
            <p className="text-sm font-semibold text-white mb-1">{user?.name}</p>
            <p className="text-xs text-gray-400">{user?.email}</p>
            <div className="mt-3 flex items-center gap-2">
              <span className={`${roleConfig.color} px-3 py-1 rounded text-xs text-white font-semibold`}>
                {roleConfig.label}
              </span>
              <span className="text-xs text-gray-500">ID: {user?.id}</span>
            </div>
          </div>

          {/* Role Info */}
          <div className="p-4 bg-gray-700/30 text-xs text-gray-300 border-b border-gray-700">
            <p className="font-semibold mb-2">Rôle actuel:</p>
            <p>{getRoleDescription(user?.role || 'admin')}</p>
          </div>

          {/* Logout Button */}
          <button
            onClick={() => {
              setIsOpen(false);
              onLogout();
            }}
            className="w-full flex items-center gap-2 px-4 py-3 text-red-400 hover:bg-gray-700 transition-colors text-sm font-medium"
          >
            <LogOut size={16} />
            Déconnexion
          </button>
        </div>
      )}
    </div>
  );
};

function getRoleDescription(role: string): string {
  const descriptions: Record<string, string> = {
    manager: 'Gestion des délégués, territoires et performance',
    marketing: 'Segmentation, campagnes et ROI marketing',
    direction: 'Tableau de bord exécutif et KPIs stratégiques',
    admin: 'Accès administrateur complet',
  };
  return descriptions[role] || 'Rôle utilisateur';
}
