import React from 'react';

interface Pill {
  variant: 'ok' | 'warn' | 'bad' | 'info';
  text: string;
}

export const Pill: React.FC<Pill> = ({ variant, text }) => {
  const getColor = () => {
    if (variant === 'ok') return 'bg-green-100 text-green-700';
    if (variant === 'warn') return 'bg-yellow-100 text-yellow-700';
    if (variant === 'bad') return 'bg-red-100 text-red-700';
    return 'bg-blue-100 text-blue-700';
  };

  return <span className={`px-2 py-1 rounded text-xs font-semibold ${getColor()}`}>{text}</span>;
};
