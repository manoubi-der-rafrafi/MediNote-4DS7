import React from 'react';

interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: number;
  deltaType?: 'up' | 'down';
  color?: string;
  sparkData?: number[];
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  unit,
  delta,
  deltaType = 'up',
  color = 'manager',
  sparkData = [],
}) => {
  const deltaColor = deltaType === 'up' ? 'text-green' : 'text-red';
  const deltaSymbol = deltaType === 'up' ? '↑' : '↓';

  return (
    <div className="bg-s1 border border-bd rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-400">{label}</p>
        {delta !== undefined && (
          <span className={`text-xs font-semibold ${deltaColor}`}>
            {deltaSymbol} {Math.abs(delta)}%
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold text-${color}`}>{value}</span>
        {unit && <span className="text-gray-500 text-sm">{unit}</span>}
      </div>

      {sparkData.length > 0 && (
        <div className="mt-3 h-8 bg-s2 rounded flex items-end gap-0.5 px-1">
          {sparkData.slice(-12).map((v, i) => (
            <div
              key={i}
              className={`flex-1 bg-${color} opacity-60`}
              style={{ height: `${(v / 100) * 100}%` }}
            />
          ))}
        </div>
      )}
    </div>
  );
};
