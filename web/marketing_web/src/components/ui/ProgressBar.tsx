import React from 'react';

interface ProgressBarProps {
  label: string;
  value: number;
  max: number;
  color?: string;
  unit?: string;
  showPercentage?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  label,
  value,
  max,
  color = 'marketing',
  unit = '',
  showPercentage = true,
}) => {
  const percentage = (value / max) * 100;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-gray-300">{label}</label>
        <span className="text-xs text-gray-500">
          {value} {unit}
          {showPercentage && ` (${Math.round(percentage)}%)`}
        </span>
      </div>
      <div className="w-full h-2 bg-s3 rounded-full overflow-hidden">
        <div
          className={`h-full bg-${color} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
