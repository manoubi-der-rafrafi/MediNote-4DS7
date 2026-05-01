// Page: ROI — App: Marketing — API: /api/v1/marketing/roi
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '../components/ui/PageHeader';
import { KpiCard } from '../components/ui/KpiCard';
import { Badge } from '../components/ui/Badge';
import { DataTable, DataTableColumn } from '../components/ui/DataTable';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../lib/api';

interface Animation {
  id: string;
  name: string;
  cost: number;
  caBefore: number;
  caAfter: number;
  roi: number;
  verdict: 'EXCELLENT' | 'BON' | 'MOYEN' | 'NÉGATIF';
}

const beforeAfterData = [
  { product: 'Animation 1', before: 0, after: 0 },
  { product: 'Animation 2', before: 0, after: 0 },
  { product: 'Animation 3', before: 0, after: 0 },
];

const regionData = [
  { region: 'Casablanca', roi: 280 },
  { region: 'Rabat', roi: 210 },
  { region: 'Marrakech', roi: 185 },
  { region: 'Fès', roi: 165 },
];

export const ROIPage: React.FC = () => {
  const [selectedCampaign] = useState('DS8');

  const visitId = 123;
  const { data: predictionResponse } = useQuery({
    queryKey: ['marketing-roi', visitId],
    queryFn: () => api.get(`/predictions/${visitId}?role=marketing`).then((r) => r.data),
  });

  const payload = predictionResponse?.data || predictionResponse || {};
  const campaignPerformance = payload?.campaign_performance || {};
  const topPerformers = campaignPerformance?.top_performers || [];

  const animations: Animation[] = topPerformers.map((item: any, idx: number) => {
    const roi = Number(item?.roi_ratio ?? item?.avg_roi_ratio ?? 0);
    return {
      id: String(item?.campaign_id ?? item?.animation_id ?? idx + 1),
      name: String(item?.campaign ?? item?.animation ?? item?.theme ?? `Campaign ${idx + 1}`),
      cost: Number(item?.cost ?? 0),
      caBefore: Number(item?.ca_before ?? 0),
      caAfter: Number(item?.ca_after ?? 0),
      roi,
      verdict: roi >= 250 ? 'EXCELLENT' : roi >= 150 ? 'BON' : roi >= 50 ? 'MOYEN' : 'NÉGATIF',
    };
  });

  const totalROI = Number(campaignPerformance?.best_roi || 0);
  const totalCA = animations.reduce((sum, a) => sum + (a.caAfter - a.caBefore), 0);
  const activeCampaigns = Number(campaignPerformance?.active_campaigns || 0);

  const columns: DataTableColumn<Animation>[] = [
    { key: 'name', label: 'Animation' },
    {
      key: 'cost',
      label: 'Coût',
      render: (v: number) => `${(v / 1000).toFixed(0)}K MAD`,
    },
    {
      key: 'caBefore',
      label: 'CA avant',
      render: (v: number) => `${(v / 1000).toFixed(0)}K MAD`,
    },
    {
      key: 'caAfter',
      label: 'CA après',
      render: (v: number) => `${(v / 1000).toFixed(0)}K MAD`,
    },
    {
      key: 'roi',
      label: 'ROI%',
      render: (v: number) => <span className={v > 0 ? 'text-green' : 'text-red'}>{v}%</span>,
    },
    {
      key: 'verdict',
      label: 'Verdict',
      render: (v: string) => (
        <Badge
          variant={
            v === 'EXCELLENT' ? 'success' : v === 'BON' ? 'info' : v === 'MOYEN' ? 'warning' : 'danger'
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
        title="ROI Animations"
        subtitle="Modèle ROI · DS8"
      />

      {/* Campaign Selector */}
      <div className="mb-6 flex gap-4 items-center">
        <label className="text-sm font-semibold text-gray-400">Campagne:</label>
        <select
          value={selectedCampaign}
          className="px-4 py-2 bg-s1 border border-bd rounded-lg text-sm text-white focus:outline-none focus:border-marketing"
        >
          <option>DS8</option>
          <option>DS9</option>
          <option>DS10</option>
        </select>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <KpiCard
          label="ROI global"
          value={`${totalROI.toFixed(0)}%`}
          delta={totalROI > 100 ? 15 : -5}
          deltaType={totalROI > 100 ? 'up' : 'down'}
          color="marketing"
        />
        <KpiCard
          label="CA généré"
          value={`${(totalCA / 1000000).toFixed(2)}M`}
          unit="MAD"
          delta={18}
          deltaType="up"
          color="marketing"
        />
        <KpiCard
          label="Campagnes actives"
          value={`${activeCampaigns}`}
          delta={0}
          deltaType="up"
          color="marketing"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Before/After */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">CA Avant / Après</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={beforeAfterData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A35" />
              <XAxis dataKey="product" stroke="#A0A0B0" style={{ fontSize: '12px' }} />
              <YAxis stroke="#A0A0B0" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  background: '#22222A',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              />
              <Legend />
              <Bar dataKey="before" fill="#666" name="Avant" />
              <Bar dataKey="after" fill="#FB923C" name="Après" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ROI by Region */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">ROI par région</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={regionData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A35" />
              <XAxis type="number" stroke="#A0A0B0" style={{ fontSize: '12px' }} />
              <YAxis dataKey="region" type="category" stroke="#A0A0B0" style={{ fontSize: '12px' }} width={80} />
              <Tooltip
                contentStyle={{
                  background: '#22222A',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              />
              <Bar dataKey="roi" fill="#FB923C" name="ROI %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Animations Table */}
      <h3 className="text-lg font-semibold mb-4">Détail par animation</h3>
      <DataTable
        columns={columns}
        data={animations}
        pageSize={10}
      />
    </div>
  );
};
