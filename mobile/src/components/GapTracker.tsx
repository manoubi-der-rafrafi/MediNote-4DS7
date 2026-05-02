import React from 'react';

interface GapTrackerProps {
  filled: number;
  labelLeft: string;
  labelRight: string;
  noteLeft: string;
  noteRight: string;
}

export const GapTracker: React.FC<GapTrackerProps> = ({ filled, labelLeft, labelRight, noteLeft, noteRight }) => {
  return (
    <div className="space-y-1">
      <div className="relative h-9 rounded overflow-hidden" style={{ backgroundColor: '#F0EEEA' }}>
        <div
          className="absolute inset-y-0 left-0 h-full"
          style={{ width: `${Math.min(100, filled)}%`, background: 'linear-gradient(90deg, var(--brand), var(--brand-2))' }}
        />
        <div className="absolute inset-0 flex items-center justify-between px-2">
          <span className="text-xs font-medium text-white blend-difference">{labelLeft}</span>
          <span className="text-xs font-medium text-[var(--muted)]">{labelRight}</span>
        </div>
      </div>
      <div className="flex justify-between">
        <span className="text-[10.5px] text-[var(--muted)]">{noteLeft}</span>
        <span className="text-[10.5px] text-[var(--muted)]">{noteRight}</span>
      </div>
    </div>
  );
};
