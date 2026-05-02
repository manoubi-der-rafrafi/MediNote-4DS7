import React from 'react';

interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaType?: 'up' | 'dn' | 'neutral';
}

export const KpiCard: React.FC<KpiCardProps> = ({ label, value, delta, deltaType = 'neutral' }) => {
  const deltaColor = deltaType === 'up' ? 'var(--pos)' : deltaType === 'dn' ? 'var(--neg)' : 'var(--muted)';

  return (
    <div
      className="p-3 rounded-lg flex-1 min-w-[45%]"
      style={{
        backgroundColor: 'var(--card)',
        border: '0.5px solid var(--border)',
        borderRadius: 'var(--radius)',
      }}
    >
      <p className="text-[10px] uppercase text-[var(--muted)]">{label}</p>
      <p className="text-[20px] font-normal text-[var(--text)] mt-1.5">{value}</p>
      {delta && <p className="text-[10.5px] mt-1" style={{ color: deltaColor }}>{delta}</p>}
    </div>
  );
};
