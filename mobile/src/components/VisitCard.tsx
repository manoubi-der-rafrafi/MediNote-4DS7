import React from 'react';
import { TierBadge } from './TierBadge';
import { Chip } from './Chip';

interface VisitCardProps {
  name: string;
  location: string;
  date: string;
  time: string;
  delegate: string;
  tier: 'A' | 'B' | 'C' | 'D';
  chips: { label: string; variant: 'pos' | 'neg' | 'warn' | 'br' | 'default' }[];
}

export const VisitCard: React.FC<VisitCardProps> = ({ name, location, date, time, delegate, tier, chips }) => {
  return (
    <div
      className="p-3 mb-2"
      style={{
        backgroundColor: 'var(--card)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
      }}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[12.5px] font-medium text-[var(--text)]">{name}</p>
          <p className="text-[10.5px] text-[var(--muted)]">{location} · {date} · {time} · {delegate}</p>
        </div>
        <TierBadge tier={tier} />
      </div>
      <div className="flex flex-wrap gap-1.5 mt-2">
        {chips.map((chip, index) => (
          <Chip key={index} label={chip.label} variant={chip.variant} />
        ))}
      </div>
    </div>
  );
};
