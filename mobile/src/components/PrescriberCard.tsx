import React from 'react';
import { Avatar } from './Avatar';
import { TierBadge } from './TierBadge';

interface PrescriberCardProps {
  name: string;
  specialty: string;
  location: string;
  tier: 'A' | 'B' | 'C' | 'D';
  prescriptions: string;
  score: string;
  lastVisit: string;
}

export const PrescriberCard: React.FC<PrescriberCardProps> = ({ name, specialty, location, tier, prescriptions, score, lastVisit }) => {
  return (
    <div
      className="p-3 mb-2"
      style={{
        backgroundColor: 'var(--card)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
      }}
    >
      <div className="flex items-center gap-3">
        <Avatar initials={name.split(' ').map(n => n[0]).join('').slice(0, 2)} size={40} />
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[12.5px] font-medium text-[var(--text)]">{name}</p>
              <p className="text-[10.5px] text-[var(--muted)]">{specialty} · {location}</p>
            </div>
            <TierBadge tier={tier} />
          </div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 mt-3 pt-2.5 border-t border-[var(--border)]">
        <div className="text-center">
          <p className="text-[13px] font-medium text-[var(--text)]">{prescriptions}</p>
          <p className="text-[10px] text-[var(--muted)]">Prescriptions</p>
        </div>
        <div className="text-center">
          <p className="text-[13px] font-medium text-[var(--text)]">{score}</p>
          <p className="text-[10px] text-[var(--muted)]">Score</p>
        </div>
        <div className="text-center">
          <p className="text-[13px] font-medium text-[var(--text)]">{lastVisit}</p>
          <p className="text-[10px] text-[var(--muted)]">Dernière visite</p>
        </div>
      </div>
    </div>
  );
};
