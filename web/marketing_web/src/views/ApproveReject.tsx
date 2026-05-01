import React, { useState } from 'react';
import { KpiCard } from '../components/KpiCard';
import { ApproveRow } from '../components/ApproveRow';

interface PendingRequest {
  id: number;
  name: string;
  meta: string;
  score: number;
  scoreClass: 'ok' | 'info' | 'warn' | 'bad';
  approved: boolean;
  rejected: boolean;
}

const initialRequests: PendingRequest[] = [
  { id: 1, name: 'Formation γ-4 (nouveau)', meta: 'Training · Tunis · 135K DT · 4wk', score: 0.96, scoreClass: 'ok', approved: false, rejected: false },
  { id: 2, name: 'Journée pédiatrie Nord', meta: 'Event · Ariana · 98K DT · 1wk', score: 0.91, scoreClass: 'ok', approved: false, rejected: false },
  { id: 3, name: 'Kit vitrine Q3 été', meta: 'PLV · All zones · 52K DT · 8wk', score: 0.84, scoreClass: 'ok', approved: false, rejected: false },
  { id: 4, name: 'Campagne TV régionale', meta: 'Promo · Sousse · 180K DT · 3wk', score: 0.78, scoreClass: 'ok', approved: false, rejected: false },
  { id: 5, name: 'Webinaire Y cardio', meta: 'Digital · National · 28K DT · 2wk', score: 0.71, scoreClass: 'info', approved: false, rejected: false },
  { id: 6, name: 'Forum hépato', meta: 'Event · Sfax · 72K DT · 1wk', score: 0.68, scoreClass: 'info', approved: false, rejected: false },
  { id: 7, name: 'Concours B (repeat)', meta: 'Contest · Tier B · 65K DT · 4wk', score: 0.58, scoreClass: 'warn', approved: false, rejected: false },
  { id: 8, name: 'Salon régional Sud-Est', meta: 'Event · Médenine · 58K DT · 2wk', score: 0.44, scoreClass: 'warn', approved: false, rejected: false },
  { id: 9, name: 'Gratuité nouvelle gamme', meta: 'Promo · All · 95K DT · 6wk', score: 0.42, scoreClass: 'warn', approved: false, rejected: false },
  { id: 10, name: 'Concours D pharmacies', meta: 'Contest · Tier D · 42K DT · 3wk', score: 0.28, scoreClass: 'bad', approved: false, rejected: false },
  { id: 11, name: 'Salon Sud-Ouest', meta: 'Event · Gafsa · 48K DT · 1wk', score: 0.22, scoreClass: 'bad', approved: false, rejected: false },
  { id: 12, name: 'Newsletter Q2', meta: 'Digital · All · 12K DT · 12wk', score: 0.31, scoreClass: 'bad', approved: false, rejected: false },
];

export const ApproveReject: React.FC = () => {
  const [requests, setRequests] = useState(initialRequests);

  const pendingCount = requests.filter((r) => !r.approved && !r.rejected).length;
  const autoScoreHigh = requests.filter((r) => r.score > 0.8 && !r.approved && !r.rejected).length;
  const autoScoreLow = requests.filter((r) => r.score < 0.4 && !r.approved && !r.rejected).length;

  const kpis = [
    { label: 'Pending', value: String(pendingCount), delta: -1, deltaType: 'down' as const, barPercent: (pendingCount / initialRequests.length) * 100, barColor: 'bg-warn' },
    { label: 'Auto-score >0.8', value: String(autoScoreHigh), delta: 0, deltaType: 'up' as const, barPercent: (autoScoreHigh / initialRequests.length) * 100, barColor: 'bg-ok' },
    { label: 'Auto-score <0.4', value: String(autoScoreLow), delta: 0, deltaType: 'down' as const, barPercent: (autoScoreLow / initialRequests.length) * 100, barColor: 'bg-bad' },
    { label: 'Total budget', value: '840K DT', delta: 0, deltaType: 'up' as const, barPercent: 100, barColor: 'bg-brand' },
  ];

  const handleApprove = (id: number) => {
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, approved: true, rejected: false } : r))
    );
  };

  const handleReject = (id: number) => {
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, approved: false, rejected: true } : r))
    );
  };

  const sortedRequests = [...requests].sort((a, b) => b.score - a.score);

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">Approve / Reject</h1>
      <p className="text-mute text-sm mb-6">Pending animation requests awaiting final approval</p>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {kpis.map((kpi, idx) => (
          <KpiCard
            key={idx}
            label={kpi.label}
            value={kpi.value}
            delta={kpi.delta}
            deltaType={kpi.deltaType || 'up'}
            barPercent={kpi.barPercent}
            barColor={kpi.barColor}
          />
        ))}
      </div>

      {/* Requests Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Pending requests</h3>
        {sortedRequests.map((request) => (
          <ApproveRow
            key={request.id}
            name={request.name}
            meta={request.meta}
            score={request.score}
            scoreClass={request.scoreClass}
            onApprove={() => handleApprove(request.id)}
            onReject={() => handleReject(request.id)}
            approved={request.approved}
            rejected={request.rejected}
          />
        ))}
      </div>
    </div>
  );
};
