// Page: Team — App: Manager — API: /api/v1/manager/team/delegates
import React, { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { DataTable, DataTableColumn } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { RingChart } from '../components/ui/RingChart';
import { Download } from 'lucide-react';

interface Delegate {
  id: string;
  name: string;
  score: number;
  delta: number;
  tier: 'A' | 'B' | 'C' | 'D';
  visits: number;
  lastActivity: string;
  avatar?: string;
}

interface DelegateDetail extends Delegate {
  scoreBreakdown: {
    notes: number;
    commission: number;
    caph: number;
    quality: number;
    nlp: number;
  };
  recentVisits: { date: string; count: number }[];
}

const mockDelegates: Delegate[] = [
  {
    id: '1',
    name: 'Ahmed Bennani',
    score: 87,
    delta: 5,
    tier: 'A',
    visits: 24,
    lastActivity: '2 hours ago',
  },
  {
    id: '2',
    name: 'Fatima El Idrissi',
    score: 82,
    delta: 2,
    tier: 'A',
    visits: 22,
    lastActivity: '4 hours ago',
  },
  {
    id: '3',
    name: 'Mohammed Karim',
    score: 76,
    delta: -1,
    tier: 'B',
    visits: 19,
    lastActivity: '1 day ago',
  },
  {
    id: '4',
    name: 'Nadia Laroui',
    score: 71,
    delta: 3,
    tier: 'B',
    visits: 18,
    lastActivity: '3 hours ago',
  },
];

const mockDelegateDetail: DelegateDetail = {
  id: '1',
  name: 'Ahmed Bennani',
  score: 87,
  delta: 5,
  tier: 'A',
  visits: 24,
  lastActivity: '2 hours ago',
  scoreBreakdown: {
    notes: 92,
    commission: 85,
    caph: 88,
    quality: 82,
    nlp: 87,
  },
  recentVisits: [
    { date: 'Lun', count: 5 },
    { date: 'Mar', count: 4 },
    { date: 'Mer', count: 5 },
    { date: 'Jeu', count: 4 },
    { date: 'Ven', count: 6 },
    { date: 'Sam', count: 0 },
    { date: 'Dim', count: 0 },
  ],
};

export const TeamPage: React.FC = () => {
  const [selectedDelegate, setSelectedDelegate] = useState<DelegateDetail | null>(null);

  const columns: DataTableColumn<Delegate>[] = [
    {
      key: 'name',
      label: 'Délégué',
      render: (v: string, _row: Delegate) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-manager rounded-full flex items-center justify-center text-xs font-bold">
            {v.split(' ').map(n => n[0]).join('')}
          </div>
          <span>{v}</span>
        </div>
      ),
    },
    {
      key: 'score',
      label: 'Score',
      render: (v: number, row: Delegate) => (
        <div className="flex items-center gap-2">
          <div className="flex-1">
            <div className="w-16 h-2 bg-s3 rounded-full overflow-hidden">
              <div className="h-full bg-manager" style={{ width: `${(v / 100) * 100}%` }} />
            </div>
          </div>
          <span className="text-sm font-semibold">{v}</span>
          <Badge variant={row.delta > 0 ? 'success' : 'danger'}>
            {row.delta > 0 ? '+' : ''}{row.delta}
          </Badge>
        </div>
      ),
    },
    {
      key: 'tier',
      label: 'Tier',
      render: (v: string) => <Badge variant={`tier-${v.toLowerCase()}` as any}>Tier {v}</Badge>,
    },
    {
      key: 'visits',
      label: 'Visites',
      render: (v: number) => `${v} ce mois`,
    },
    {
      key: 'lastActivity',
      label: 'Dernière activité',
      render: (v: string) => <span className="text-gray-400 text-sm">{v}</span>,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Mon équipe"
        subtitle="Performance de vos délégués"
        action={{
          label: 'Exporter CSV',
          icon: <Download size={16} />,
          onClick: () => alert('Export CSV'),
        }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table */}
        <div className="lg:col-span-2">
          <DataTable
            columns={columns}
            data={mockDelegates}
            pageSize={10}
            onRowClick={_row => {
              // In real app, fetch delegate details
              setSelectedDelegate(mockDelegateDetail);
            }}
          />
        </div>

        {/* Detail Panel */}
        {selectedDelegate && (
          <div className="bg-s1 border border-bd rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{selectedDelegate.name}</h3>
              <button
                onClick={() => setSelectedDelegate(null)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            <div className="flex justify-center mb-6">
              <RingChart
                progress={selectedDelegate.score}
                color="purple"
                size={120}
                label={`Score: ${selectedDelegate.score}/100`}
                sublabel={`Tier ${selectedDelegate.tier}`}
              />
            </div>

            <div className="space-y-3 mb-6">
              <ProgressBar
                label="Notes (KPI)"
                value={selectedDelegate.scoreBreakdown.notes}
                max={100}
                color="purple"
                unit="/100"
              />
              <ProgressBar
                label="Commission"
                value={selectedDelegate.scoreBreakdown.commission}
                max={100}
                color="purple"
                unit="/100"
              />
              <ProgressBar
                label="CAPH"
                value={selectedDelegate.scoreBreakdown.caph}
                max={100}
                color="purple"
                unit="/100"
              />
              <ProgressBar
                label="Qualité visite"
                value={selectedDelegate.scoreBreakdown.quality}
                max={100}
                color="purple"
                unit="/100"
              />
              <ProgressBar
                label="Sentiment NLP"
                value={selectedDelegate.scoreBreakdown.nlp}
                max={100}
                color="purple"
                unit="/100"
              />
            </div>

            <button className="w-full px-4 py-2 bg-manager text-white rounded-lg hover:opacity-90 transition-opacity text-sm font-semibold">
              Voir coaching
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
