import React from 'react';
import { Chip } from './Chip';

interface ProspectCardProps {
  name: string;
  meta: string[];
  score: number;
  hot?: boolean;
}

export const ProspectCard: React.FC<ProspectCardProps> = ({ name, meta, score, hot = false }) => {
  return (
    <div
      className="relative p-3 mb-2 rounded-lg"
      style={{
        backgroundColor: hot ? 'var(--brand-soft)' : 'var(--card)',
        border: `0.5px solid ${hot ? 'var(--brand)' : 'var(--border)'}`,
        borderRadius: '12px',
      }}
    >
      <div className="absolute top-2 right-2">
        <span
          className="inline-block px-2 py-0.5 text-[10.5px] font-medium text-white rounded-full"
          style={{ backgroundColor: score >= 0.75 ? 'var(--brand)' : 'var(--warn)' }}
        >
          {score}
        </span>
      </div>
      <p className="text-[12.5px] font-medium text-[var(--text)] pr-12">{name}</p>
      <div className="flex flex-wrap gap-2.5 mt-1">
        {meta.map((m, i) => (
          <span key={i} className="text-[11px] text-[var(--muted)]">{m}</span>
        ))}
      </div>
    </div>
  );
};
