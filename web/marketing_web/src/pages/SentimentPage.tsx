// Page: Sentiment — App: Marketing — API: /api/v1/marketing/sentiment
import React, { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { RingChart } from '../components/ui/RingChart';
import { DataTable, DataTableColumn } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Animation {
  id: string;
  name: string;
  date: string;
  sentiment: number;
  flags: string[];
  visits: number;
}

const mockAnimations: Animation[] = [
  { id: '1', name: 'Paracétamol Summer', date: '2026-04-10', sentiment: 0.45, flags: ['OBJECTION_PRIX', 'DEMANDE_ETUDE'], visits: 24 },
  { id: '2', name: 'Ibuprofène Promo', date: '2026-04-08', sentiment: 0.62, flags: ['INTERET_PRODUIT', 'URGENCE_ORDONNANCE'], visits: 18 },
];

const sentimentTrend = [
  { date: '10 Apr', sentiment: 0.68 },
  { date: '11 Apr', sentiment: 0.65 },
  { date: '12 Apr', sentiment: 0.62 },
  { date: '13 Apr', sentiment: 0.70 },
  { date: '14 Apr', sentiment: 0.74 },
];

const flags = [
  { label: 'INTERET_PRODUIT', count: 145, percentage: 32 },
  { label: 'OBJECTION_PRIX', count: 98, percentage: 21 },
  { label: 'DEMANDE_ETUDE', count: 67, percentage: 15 },
  { label: 'SATISFACTION', count: 54, percentage: 12 },
  { label: 'URGENCE_ORDONNANCE', count: 43, percentage: 9 },
  { label: 'RELATION_STABLE', count: 32, percentage: 7 },
  { label: 'CONCURRENCE', count: 18, percentage: 3 },
  { label: 'BESOIN_FORMATION', count: 8, percentage: 1 },
];

const animationColumns: DataTableColumn<Animation>[] = [
  { key: 'name', label: 'Animation' },
  { key: 'date', label: 'Date' },
  {
    key: 'sentiment',
    label: 'Sentiment moy',
    render: (v: number) => (
      <div className="flex items-center gap-2">
        <div className="w-12 h-2 bg-s3 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-red to-green"
            style={{ width: `${v * 100}%` }}
          />
        </div>
        <span className="text-sm">{(v * 100).toFixed(0)}%</span>
      </div>
    ),
  },
  {
    key: 'flags',
    label: 'Flags top 3',
    render: (v: string[]) => (
      <div className="flex gap-1 flex-wrap">
        {v.slice(0, 3).map((flag, i) => (
          <Badge key={i} variant="info">{flag}</Badge>
        ))}
      </div>
    ),
  },
  { key: 'visits', label: 'Nb visites' },
];

type Period = '7d' | '30d' | '90d';

export const SentimentPage: React.FC = () => {
  const [period, setPeriod] = useState<Period>('30d');

  return (
    <div>
      <PageHeader
        title="Analyse Sentiment NLP"
        subtitle="CamemBERT · Nb12"
      />

      {/* Period Filter */}
      <div className="mb-6 flex gap-2">
        {(['7d', '30d', '90d'] as Period[]).map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
              period === p
                ? 'bg-marketing text-white'
                : 'bg-s2 text-gray-300 hover:bg-s3'
            }`}
          >
            {p === '7d' ? '7 jours' : p === '30d' ? '30 jours' : '90 jours'}
          </button>
        ))}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {/* Global Score */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Score global</h3>
          <div className="flex justify-center mb-4">
            <RingChart
              progress={74}
              color="orange"
              size={120}
              label="74% positif"
              sublabel="26% négatif"
            />
          </div>
        </div>

        {/* Trend */}
        <div className="lg:col-span-2 bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Tendance sentiment</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={sentimentTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A35" />
              <XAxis dataKey="date" stroke="#A0A0B0" style={{ fontSize: '12px' }} />
              <YAxis stroke="#A0A0B0" style={{ fontSize: '12px' }} domain={[0, 1]} />
              <Tooltip
                contentStyle={{
                  background: '#22222A',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              />
              <Line
                type="monotone"
                dataKey="sentiment"
                stroke="#FB923C"
                dot={{ fill: '#FB923C', r: 3 }}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Flags Breakdown */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Flags NLP détectés</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {flags.map(flag => (
            <div key={flag.label} className="bg-s1 border border-bd rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-300">{flag.label}</span>
                <Badge variant="info">{flag.percentage}%</Badge>
              </div>
              <div className="text-lg font-bold text-marketing mb-2">{flag.count}</div>
              <ProgressBar
                label="Occurrence"
                value={flag.percentage}
                max={100}
                color="marketing"
                showPercentage={false}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Animations Table */}
      <h3 className="text-lg font-semibold mb-4">Sentiment par animation</h3>
      <DataTable
        columns={animationColumns}
        data={mockAnimations}
        pageSize={10}
      />
    </div>
  );
};
