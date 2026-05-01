interface KpiCardProps {
  label: string;
  value: string;
  delta?: number;
  deltaType?: 'up' | 'down' | 'warn' | 'neutral';
  barPercent?: number;
  barColor?: string;
}

export function KpiCard({
  label,
  value,
  delta,
  deltaType = 'neutral',
  barPercent = 0,
  barColor = 'bg-brand',
}: KpiCardProps) {
  const getDeltaColor = () => {
    if (deltaType === 'up') return 'text-ok';
    if (deltaType === 'down') return 'text-bad';
    if (deltaType === 'warn') return 'text-warn';
    return 'text-mute';
  };

  const getDeltaIcon = () => {
    if (deltaType === 'up') return '▲';
    if (deltaType === 'down') return '▼';
    return '';
  };

  return (
    <div className="bg-card rounded-lg p-4 border border-line">
      <div className="text-xs font-semibold uppercase tracking-wider text-mute mb-2">
        {label}
      </div>
      <div className="text-24 font-bold text-ink mb-3">{value}</div>

      {delta !== undefined && (
        <div className={`text-sm font-semibold mb-3 ${getDeltaColor()}`}>
          {getDeltaIcon()} {delta > 0 ? '+' : ''}{delta}
        </div>
      )}

      {barPercent !== undefined && (
        <div className="w-full h-1.5 bg-line rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${barPercent}%` }}
          />
        </div>
      )}
    </div>
  );
}
