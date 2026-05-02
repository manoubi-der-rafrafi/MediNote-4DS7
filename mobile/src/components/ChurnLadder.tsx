import React from 'react';
import { Chip } from './Chip';

interface ChurnLevel {
  label: string;
  description: string;
  count: number;
  variant: 'pos' | 'neg' | 'warn' | 'br' | 'default';
}

interface ChurnLadderProps {
  levels: ChurnLevel[];
}

export const ChurnLadder: React.FC<ChurnLadderProps> = ({ levels }) => {
  const levelStyles = [
    { bg: 'rgba(184, 134, 11, 0.08)' },
    { bg: 'rgba(185, 74, 72, 0.08)' },
    { bg: '#F4F3EE' },
  ];

  const dotColors = ['var(--warn)', 'var(--neg)', 'var(--muted)'];

  return (
    <div className="space-y-2">
      {levels.map((level, index) => (
        <div
          key={index}
          className="flex items-center justify-between p-3 rounded-lg"
          style={{ backgroundColor: levelStyles[index].bg }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor: index < 2 ? dotColors[index] : 'transparent',
                border: index === 2 ? '1.5px solid var(--muted)' : 'none',
              }}
            />
            <div>
              <p className="text-[12.5px] font-medium text-[var(--text)]">{level.label}</p>
              <p className="text-[10.5px] text-[var(--muted)]">{level.description}</p>
            </div>
          </div>
          <Chip label={level.count.toString()} variant={level.variant} />
        </div>
      ))}
    </div>
  );
};
