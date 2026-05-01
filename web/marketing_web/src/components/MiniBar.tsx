import React from 'react';

interface MiniBar {
  percent: number;
  color?: string;
}

export const MiniBar: React.FC<MiniBar> = ({ percent, color = 'bg-info' }) => {
  return (
    <div className="w-24 h-1.5 bg-line rounded overflow-hidden">
      <div className={`h-full ${color}`} style={{ width: `${Math.min(100, percent)}%` }} />
    </div>
  );
};
