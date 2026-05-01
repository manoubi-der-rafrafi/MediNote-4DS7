import React from 'react';
import { Badge } from './Badge';

interface ScenarioCardProps {
  scenario: 'pessimiste' | 'realiste' | 'optimiste';
  value: string | number;
  unit?: string;
  delta?: number;
  color: string;
  assumptions?: string[];
}

const scenarioConfig = {
  pessimiste: {
    label: 'Pessimiste',
    color: 'danger',
    bgColor: 'bg-red/10',
    textColor: 'text-red',
  },
  realiste: {
    label: 'Réaliste',
    color: 'info',
    bgColor: 'bg-blue/10',
    textColor: 'text-blue',
  },
  optimiste: {
    label: 'Optimiste',
    color: 'success',
    bgColor: 'bg-green/10',
    textColor: 'text-green',
  },
};

export const ScenarioCard: React.FC<ScenarioCardProps> = ({
  scenario,
  value,
  unit = '',
  delta,
  color,
  assumptions = [],
}) => {
  const config = scenarioConfig[scenario];

  return (
    <div className={`${config.bgColor} border border-${color}/30 rounded-lg p-4`}>
      <Badge variant={config.color as any}>{config.label}</Badge>

      <div className="mt-3 mb-2">
        <div className={`text-2xl font-bold ${config.textColor}`}>
          {value} {unit}
        </div>
        {delta !== undefined && (
          <div className="text-sm text-gray-400 mt-1">
            {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}% vs. actuel
          </div>
        )}
      </div>

      {assumptions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-bd">
          <p className="text-xs font-semibold text-gray-400 mb-2">Hypothèses</p>
          <ul className="space-y-1">
            {assumptions.map((assumption, i) => (
              <li key={i} className="text-xs text-gray-500 flex items-start gap-2">
                <span className="text-gray-600 mt-0.5">•</span>
                <span>{assumption}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
