import React from 'react';

interface ScoreBoxProps {
  score: number;
}

export const ScoreBox: React.FC<ScoreBoxProps> = ({ score }) => {
  return (
    <div className="rounded-lg p-8 text-center" style={{ background: 'var(--brand-soft)' }}>
      <div className="text-5xl font-bold text-brand mb-2">{score.toFixed(2)}</div>
      <div className="text-sm font-semibold text-mute">P(mouvement fort)</div>
    </div>
  );
};
