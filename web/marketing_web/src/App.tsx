import React, { useState } from 'react';
import { BarChart3, Zap, DollarSign, MessageSquare, Tag, Eye, CheckCircle } from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import { Dashboard } from './views/Dashboard';
import { AnimationList } from './views/AnimationList';
import { BudgetROI } from './views/BudgetROI';
import { Sentiment } from './views/Sentiment';
import { Themes } from './views/Themes';
import { Forecasts } from './views/Forecasts';
import { Eligibility } from './views/Eligibility';
import { ApproveReject } from './views/ApproveReject';

type ViewKey = 'dashboard' | 'animations' | 'budget' | 'sentiment' | 'themes' | 'forecasts' | 'eligibility' | 'approve';

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
    label: 'OVERVIEW',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 size={16} /> },
      { id: 'animations', label: '32 Animations', icon: <Zap size={16} /> },
      { id: 'budget', label: 'Budget & ROI', icon: <DollarSign size={16} /> },
    ],
  },
  {
    label: 'INTELLIGENCE',
    items: [
      { id: 'sentiment', label: 'Sentiment', icon: <MessageSquare size={16} /> },
      { id: 'themes', label: 'Themes', icon: <Tag size={16} /> },
      { id: 'forecasts', label: 'Forecasts', icon: <Eye size={16} /> },
    ],
  },
  {
    label: 'ACTIONS',
    items: [
      { id: 'eligibility', label: 'Eligibility check', icon: <CheckCircle size={16} /> },
      { id: 'approve', label: 'Approve / Reject', icon: <CheckCircle size={16} /> },
    ],
  },
];

const viewComponents = {
  dashboard: Dashboard,
  animations: AnimationList,
  budget: BudgetROI,
  sentiment: Sentiment,
  themes: Themes,
  forecasts: Forecasts,
  eligibility: Eligibility,
  approve: ApproveReject,
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
          <h1 className="text-lg font-bold">Marketing Console</h1>
          <p className="text-xs mt-1" style={{ color: '#F4C0D1' }}>Animations · v2026</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {navigationStructure.map((section, idx) => (
            <div key={idx} className="mb-6">
              <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider" style={{ color: '#F4C0D1' }}>
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
                    color: activeView === item.id ? '#ffffff' : '#F4C0D1',
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
        <div className="px-4 py-4 border-t border-white/10 text-xs" style={{ color: '#F4C0D1' }}>
          <div>© 2026 Marketing</div>
          <div className="mt-1">Updated: 18 Apr 2026</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="px-8 py-7 max-w-6xl mx-auto">
          <ViewComponent />
        </div>
      </main>
      <ChatWidget role="marketing" />
    </div>
  );
}
