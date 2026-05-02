import React from 'react';
import { KpiCard } from './KpiCard';

interface KpiData {
  label: string;
  value: string;
  delta?: string;
  deltaType?: 'up' | 'dn' | 'neutral';
}

interface KpiGridProps {
  kpis: KpiData[];
}

export const KpiGrid: React.FC<KpiGridProps> = ({ kpis }) => {
  return (
    <div className="flex flex-wrap gap-2.5 mb-3">
      {kpis.map((kpi, index) => (
        <KpiCard key={index} {...kpi} />
      ))}
    </div>
  );
};
