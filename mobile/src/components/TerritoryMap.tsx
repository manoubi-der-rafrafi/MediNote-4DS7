import React from 'react';

interface TerritoryMapProps {
  pattern: string[];
}

export const TerritoryMap: React.FC<TerritoryMapProps> = ({ pattern }) => {
  const cellStyles: Record<string, string> = {
    '': 'var(--brand-soft)',
    'mid': 'rgba(46, 125, 79, 0.35)',
    'hot': 'var(--brand)',
    'empty': '#f4f3ee',
  };

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-6 gap-1">
        {pattern.map((cell, index) => (
          <div
            key={index}
            className="aspect-square rounded"
            style={{ backgroundColor: cellStyles[cell] || 'var(--brand-soft)' }}
          />
        ))}
      </div>
      <div className="flex justify-center gap-5">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f4f3ee' }} />
          <span className="text-[10.5px] text-[var(--muted)]">Non couvert</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'var(--brand-soft)' }} />
          <span className="text-[10.5px] text-[var(--muted)]">Faible</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'var(--brand)' }} />
          <span className="text-[10.5px] text-[var(--muted)]">Forte</span>
        </div>
      </div>
    </div>
  );
};
