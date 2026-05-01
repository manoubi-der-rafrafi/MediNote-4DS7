import React from 'react';

interface KpiCardProps {
  label: string;
  value: string;
  delta?: number;
  deltaType?: 'up' | 'down' | 'warn' | 'neutral';
  barPercent?: number;
  barColor?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  delta = 0,
  deltaType = 'neutral',
  barPercent = 0,
  barColor = 'bg-brand',
}) => {
  const getDeltaColor = () => {
    if (deltaType === 'up') return 'text-ok';
    if (deltaType === 'down') return 'text-bad';
    if (deltaType === 'warn') return 'text-warn';
    return 'text-mute';
  };

  return (
    <div className="bg-card border border-line rounded p-4">
      <div className="text-xs font-semibold text-mute uppercase tracking-wide mb-2">{label}</div>
      <div className="text-2xl font-bold text-ink mb-3">{value}</div>
      {delta !== 0 && (
        <div className={`text-sm font-medium mb-3 ${getDeltaColor()}`}>
          {deltaType === 'down' ? '▼' : '▲'} {Math.abs(delta)}%
        </div>
      )}
      {barPercent !== undefined && (
        <div className="w-full bg-line rounded overflow-hidden h-1">
          <div className={`h-full ${barColor}`} style={{ width: `${Math.min(100, barPercent)}%` }} />
        </div>
      )}
    </div>
  );
};
