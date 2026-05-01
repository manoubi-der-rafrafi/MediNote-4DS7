import React from 'react';

interface RecCardProps {
  type: 'keep' | 'watch' | 'drop';
  title: string;
  subtitle: string;
}

export const RecoCard: React.FC<RecCardProps> = ({ type, title, subtitle }) => {
  const getColor = () => {
    if (type === 'keep') return { border: 'border-ok', bg: 'bg-green-50' };
    if (type === 'watch') return { border: 'border-info', bg: 'bg-blue-50' };
    return { border: 'border-bad', bg: 'bg-red-50' };
  };

  const getLabel = () => {
    if (type === 'keep') return 'KEEP';
    if (type === 'watch') return 'WATCH';
    return 'DROP';
  };

  const color = getColor();

  return (
    <div className={`border-l-4 ${color.border} ${color.bg} p-4 rounded`}>
      <div className="text-xs font-bold text-ink mb-1">{getLabel()}</div>
      <div className="text-sm font-semibold text-ink mb-1">{title}</div>
      <div className="text-xs text-mute">{subtitle}</div>
    </div>
  );
};
