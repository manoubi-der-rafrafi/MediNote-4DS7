import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string;
  delta?: number;
  deltaType?: 'up' | 'down' | 'warn';
  barPercent?: number;
  barColor?: string;
}

export function KpiCard({ label, value, delta, deltaType = 'up', barPercent = 0, barColor = 'bg-ok' }: KpiCardProps) {
  const getDeltaColor = () => {
    if (deltaType === 'up') return 'text-ok';
    if (deltaType === 'down') return 'text-bad';
    return 'text-warn';
  };

  const getDeltaIcon = () => {
    if (deltaType === 'warn') return <AlertCircle className="w-4 h-4 inline mr-1" />;
    if (deltaType === 'down') return <TrendingDown className="w-4 h-4 inline mr-1" />;
    return <TrendingUp className="w-4 h-4 inline mr-1" />;
  };

  return (
    <div className="bg-card border border-line rounded-lg p-5">
      <div className="text-label mb-2">{label}</div>
      <div className="text-kpi mb-3">{value}</div>
      {delta !== undefined && (
        <div className={`text-sm font-medium mb-2 ${getDeltaColor()}`}>
          {getDeltaIcon()}
          {Math.abs(delta)}%
        </div>
      )}
      {barPercent > 0 && (
        <div className="w-full h-1 bg-line rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor}`}
            style={{ width: `${Math.min(barPercent, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}
