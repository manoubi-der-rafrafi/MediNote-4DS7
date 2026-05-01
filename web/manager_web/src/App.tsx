import React, { useState } from 'react';
import { LayoutGrid, Users, Zap, BarChart3, AlertTriangle, Tags, Banknote, BookOpen, TrendingDown } from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import './index.css';

import { Dashboard } from './views/Dashboard';
import { Delegates } from './views/Delegates';
import { Coaching } from './views/Coaching';
import { VisitQuality } from './views/VisitQuality';
import { Anomalies } from './views/Anomalies';
import { SemanticFlags } from './views/SemanticFlags';
import { Primes } from './views/Primes';
import { Formation } from './views/Formation';
import { Attrition } from './views/Attrition';

type ViewKey = 'dashboard' | 'delegates' | 'coaching' | 'quality' | 'anomalies' | 'flags' | 'primes' | 'formation' | 'attrition';

interface NavItem {
  id: ViewKey;
  label: string;
  icon: React.ReactNode;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const navigationStructure: NavSection[] = [
  {
    label: 'MY TEAM',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: <LayoutGrid size={18} /> },
      { id: 'delegates', label: 'Delegates (18)', icon: <Users size={18} /> },
      { id: 'coaching', label: 'Coaching Queue', icon: <Zap size={18} /> },
    ],
  },
  {
    label: 'REPORTS',
    items: [
      { id: 'quality', label: 'Visit Quality', icon: <BarChart3 size={18} /> },
      { id: 'anomalies', label: 'Anomalies', icon: <AlertTriangle size={18} /> },
      { id: 'flags', label: 'Semantic Flags', icon: <Tags size={18} /> },
    ],
  },
  {
    label: 'PERFORMANCE',
    items: [
      { id: 'primes', label: 'Primes & Bonus', icon: <Banknote size={18} /> },
      { id: 'formation', label: 'Formation ROI', icon: <BookOpen size={18} /> },
      { id: 'attrition', label: 'Attrition Risk', icon: <TrendingDown size={18} /> },
    ],
  },
];

const viewComponents: Record<ViewKey, React.ComponentType> = {
  dashboard: Dashboard,
  delegates: Delegates,
  coaching: Coaching,
  quality: VisitQuality,
  anomalies: Anomalies,
  flags: SemanticFlags,
  primes: Primes,
  formation: Formation,
  attrition: Attrition,
};

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');

  const ViewComponent = viewComponents[activeView];

  return (
    <div className="flex h-screen" style={{ backgroundColor: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside className="w-56 text-white flex flex-col border-r border-line/20" style={{ backgroundColor: 'var(--brand-dark)' }}>
        {/* Brand */}
        <div className="px-6 py-5 border-b border-white/10">
          <h1 className="text-lg font-bold">Superviseur</h1>
          <p className="text-xs mt-1" style={{ color: '#FAC775' }}>Karim Belhadj · 18 delegates</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {navigationStructure.map((section, idx) => (
            <div key={idx} className="mb-6">
              <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider" style={{ color: '#FAC775' }}>
                {section.label}
              </div>
              {section.items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded text-sm font-medium transition-all ${
                    activeView === item.id
                      ? 'text-white'
                      : 'hover:bg-white/5 hover:text-white'
                  }`}
                  style={{
                    backgroundColor: activeView === item.id ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                    color: activeView === item.id ? '#ffffff' : '#FAC775',
                  }}
                >
                  <span className="flex-shrink-0 flex items-center gap-2">
                    {item.icon}
                    {activeView === item.id && <span className="w-1.5 h-1.5 bg-white rounded-full" />}
                  </span>
                  <span className="text-left">{item.label}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/10 text-xs" style={{ color: '#FAC775' }}>
          <div>© 2026 Superviseur</div>
          <div className="mt-1">Updated: 18 Apr 2026</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="px-8 py-7 max-w-6xl mx-auto">
          <ViewComponent />
        </div>
      </main>
      <ChatWidget role="supervisor" />
    </div>
  );
}
