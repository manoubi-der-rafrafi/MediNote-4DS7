// Page: Anomalies — App: Manager — API: /api/v1/manager/anomalies
import React, { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { DataTable, DataTableColumn } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Anomaly {
  id: string;
  entity: string;
  type: string;
  score: number;
  detectedAt: string;
  status: 'OUVERT' | 'RÉSOLU' | 'IGNORÉ';
  severity: 'STRONG' | 'MODERATE' | 'WEAK';
}

const mockAnomalies: Anomaly[] = [
  {
    id: '1',
    entity: 'Ahmed Bennani',
    type: 'KPI_CHUTE',
    score: 0.87,
    detectedAt: '2026-04-13',
    status: 'OUVERT',
    severity: 'STRONG',
  },
  {
    id: '2',
    entity: 'Fatima El Idrissi',
    type: 'VISITE_MANQUÉE',
    score: 0.62,
    detectedAt: '2026-04-12',
    status: 'OUVERT',
    severity: 'MODERATE',
  },
  {
    id: '3',
    entity: 'Mohammed Karim',
    type: 'QUOTA_DÉPASSE',
    score: 0.45,
    detectedAt: '2026-04-11',
    status: 'RÉSOLU',
    severity: 'WEAK',
  },
  {
    id: '4',
    entity: 'Nadia Laroui',
    type: 'KPI_CHUTE',
    score: 0.72,
    detectedAt: '2026-04-10',
    status: 'IGNORÉ',
    severity: 'STRONG',
  },
];

const timelineData = [
  { date: '10 Apr', score: 0.45 },
  { date: '11 Apr', score: 0.58 },
  { date: '12 Apr', score: 0.62 },
  { date: '13 Apr', score: 0.67 },
  { date: '14 Apr', score: 0.72 },
];

type Period = '7d' | '30d' | '90d';
type Severity = 'ALL' | 'STRONG' | 'MODERATE' | 'WEAK';
type AnomalyType = 'ALL' | 'KPI_CHUTE' | 'QUOTA_DÉPASSE' | 'VISITE_MANQUÉE';

export const AnomaliesPage: React.FC = () => {
  const [period, setPeriod] = useState<Period>('30d');
  const [severity, setSeverity] = useState<Severity>('ALL');
  const [anomalyType, setAnomalyType] = useState<AnomalyType>('ALL');

  const periods: { value: Period; label: string }[] = [
    { value: '7d', label: '7 jours' },
    { value: '30d', label: '30 jours' },
    { value: '90d', label: '90 jours' },
  ];

  const severities: { value: Severity; label: string }[] = [
    { value: 'ALL', label: 'Tous' },
    { value: 'STRONG', label: 'STRONG' },
    { value: 'MODERATE', label: 'MODERATE' },
    { value: 'WEAK', label: 'WEAK' },
  ];

  const anomalyTypes: { value: AnomalyType; label: string }[] = [
    { value: 'ALL', label: 'Tous' },
    { value: 'KPI_CHUTE', label: 'KPI_CHUTE' },
    { value: 'QUOTA_DÉPASSE', label: 'QUOTA_DÉPASSE' },
    { value: 'VISITE_MANQUÉE', label: 'VISITE_MANQUÉE' },
  ];

  const filteredAnomalies = mockAnomalies.filter(a => {
    if (severity !== 'ALL' && a.severity !== severity) return false;
    if (anomalyType !== 'ALL' && a.type !== anomalyType) return false;
    return true;
  });

  const columns: DataTableColumn<Anomaly>[] = [
    {
      key: 'entity',
      label: 'Entité',
    },
    {
      key: 'type',
      label: 'Type',
    },
    {
      key: 'score',
      label: 'Score',
      render: (v: number) => (
        <div className="flex items-center gap-2">
          <div className="w-12 h-2 bg-s3 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green to-red"
              style={{ width: `${v * 100}%` }}
            />
          </div>
          <span className="text-sm">{(v * 100).toFixed(0)}%</span>
        </div>
      ),
    },
    {
      key: 'detectedAt',
      label: 'Détecté le',
    },
    {
      key: 'status',
      label: 'Statut',
      render: (v: string) => (
        <Badge
          variant={
            v === 'RÉSOLU' ? 'success' : v === 'IGNORÉ' ? 'default' : 'warning'
          }
        >
          {v}
        </Badge>
      ),
    },
    {
      key: 'severity',
      label: 'Sévérité',
      render: (v: string) => (
        <Badge
          variant={
            v === 'STRONG' ? 'danger' : v === 'MODERATE' ? 'warning' : 'info'
          }
        >
          {v}
        </Badge>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Anomalies détectées"
        subtitle={`Total: ${filteredAnomalies.length}`}
      />

      {/* Timeline Chart */}
      <div className="bg-s1 border border-bd rounded-lg p-6 mb-6">
        <h3 className="text-sm font-semibold mb-4">Évolution des anomalies (30j)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={timelineData}>
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
              dataKey="score"
              stroke="#F87171"
              dot={{ fill: '#F87171', r: 4 }}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">
            Période
          </label>
          <div className="flex gap-2">
            {periods.map(p => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                  period === p.value
                    ? 'bg-manager text-white'
                    : 'bg-s2 text-gray-300 hover:bg-s3'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">
            Sévérité
          </label>
          <div className="flex gap-2">
            {severities.map(s => (
              <button
                key={s.value}
                onClick={() => setSeverity(s.value)}
                className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                  severity === s.value
                    ? 'bg-manager text-white'
                    : 'bg-s2 text-gray-300 hover:bg-s3'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">
            Type
          </label>
          <div className="flex gap-2">
            {anomalyTypes.map(t => (
              <button
                key={t.value}
                onClick={() => setAnomalyType(t.value)}
                className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                  anomalyType === t.value
                    ? 'bg-manager text-white'
                    : 'bg-s2 text-gray-300 hover:bg-s3'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={filteredAnomalies}
        pageSize={10}
      />
    </div>
  );
};
