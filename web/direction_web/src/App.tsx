import React, { useState } from 'react';
import { BarChart3, TrendingUp, Globe, Box, Users, Zap, Eye, AlertTriangle, Database } from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import ExecutiveDashboard from './views/Executive';
import RevenueDashboard from './views/Revenue';
import MarketDashboard from './views/Market';
import SupplyDashboard from './views/Supply';
import PeopleDashboard from './views/People';
import AnimationsDashboard from './views/Animations';
import ForecastsDashboard from './views/Forecasts';
import AnomaliesDashboard from './views/Anomalies';
import DataQualityDashboard from './views/DataQuality';

type ViewKey = 'executive' | 'revenue' | 'market' | 'supply' | 'people' | 'animations' | 'forecasts' | 'anomalies' | 'data';

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
      { id: 'executive', label: 'Executive Dashboard', icon: <BarChart3 size={16} /> },
      { id: 'revenue', label: 'Revenue & Finance', icon: <TrendingUp size={16} /> },
      { id: 'market', label: 'Market & Geography', icon: <Globe size={16} /> },
    ],
  },
  {
    label: 'OPERATIONS',
    items: [
      { id: 'supply', label: 'Supply & Stock', icon: <Box size={16} /> },
      { id: 'people', label: 'People & Delegates', icon: <Users size={16} /> },
      { id: 'animations', label: 'Animations', icon: <Zap size={16} /> },
    ],
  },
  {
    label: 'INTELLIGENCE',
    items: [
      { id: 'forecasts', label: 'Forecasts', icon: <Eye size={16} /> },
      { id: 'anomalies', label: 'Anomalies & Alerts', icon: <AlertTriangle size={16} /> },
      { id: 'data', label: 'Data Quality & IT', icon: <Database size={16} /> },
    ],
  },
];

const viewComponents = {
  executive: ExecutiveDashboard,
  revenue: RevenueDashboard,
  market: MarketDashboard,
  supply: SupplyDashboard,
  people: PeopleDashboard,
  animations: AnimationsDashboard,
  forecasts: ForecastsDashboard,
  anomalies: AnomaliesDashboard,
  data: DataQualityDashboard,
};

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>('executive');

  const ViewComponent = viewComponents[activeView];

  return (
    <div className="flex h-screen bg-bg">
      {/* Sidebar */}
      <aside className="w-56 bg-sidebar-bg text-white flex flex-col border-r border-line/20">
        {/* Brand */}
        <div className="px-6 py-5 border-b border-white/10">
          <h1 className="text-lg font-bold">Pharma Analytics</h1>
          <p className="text-xs text-gray-400 mt-1">Founder console · v2026</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {navigationStructure.map((section, idx) => (
            <div key={idx} className="mb-6">
              <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {section.label}
              </div>
              {section.items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded text-sm font-medium transition-all ${
                    activeView === item.id
                      ? 'bg-white/15 text-white'
                      : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <span className="flex-shrink-0">{item.icon}</span>
                  <span className="text-left">{item.label}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/10 text-xs text-gray-400">
          <div>© 2026 Pharma Analytics</div>
          <div className="mt-1">Data updated: 18 Apr 2026</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="px-8 py-7 max-w-6xl mx-auto">
          <ViewComponent />
        </div>
      </main>
      <ChatWidget role="founder" />
    </div>
  );
}
