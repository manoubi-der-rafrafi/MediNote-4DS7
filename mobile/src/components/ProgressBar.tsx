import React from 'react';

interface ProgressBarProps {
  percent: number;
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ percent, color = 'var(--brand)' }) => {
  return (
    <div className="h-1.5 rounded mt-1.5" style={{ backgroundColor: '#F0EEEA', overflow: 'hidden' }}>
      <div
        className="h-full rounded"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%`, backgroundColor: color }}
      />
    </div>
  );
};
