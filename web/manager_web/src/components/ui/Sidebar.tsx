import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LucideIcon } from 'lucide-react';

interface SidebarItem {
  icon: LucideIcon;
  label: string;
  path: string;
}

interface SidebarProps {
  items: SidebarItem[];
  brandColor: string;
  role: string;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ items, brandColor, role, onLogout }) => {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-s1 border-r border-bd flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-bd">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 bg-${brandColor} rounded-lg`} />
          <div>
            <h2 className="font-bold text-white">CRM Pharma</h2>
            <p className="text-xs text-gray-400 capitalize">{role}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {items.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? `bg-${brandColor}/20 text-${brandColor} border border-${brandColor}/30`
                  : 'text-gray-400 hover:bg-s2'
              }`}
            >
              <Icon size={20} />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-bd">
        <button
          onClick={onLogout}
          className="w-full px-4 py-2 bg-red/15 text-red rounded-lg hover:bg-red/25 transition-colors text-sm font-semibold"
        >
          Déconnexion
        </button>
      </div>
    </aside>
  );
};
