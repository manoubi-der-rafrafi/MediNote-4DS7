import React from 'react';

interface SentimentSampleProps {
  type: 'pos' | 'neu' | 'neg';
  quote: string;
  meta: string;
}

export const SentimentSample: React.FC<SentimentSampleProps> = ({ type, quote, meta }) => {
  const getColor = () => {
    if (type === 'pos') return { border: 'border-ok', bg: 'bg-green-50' };
    if (type === 'neu') return { border: 'border-brand', bg: 'bg-brand-soft' };
    return { border: 'border-bad', bg: 'bg-red-50' };
  };

  const color = getColor();

  return (
    <div className={`border-l-4 ${color.border} ${color.bg} p-3 rounded mb-3`}>
      <p className="text-sm text-ink mb-2 italic">"{quote}"</p>
      <p className="text-xs text-mute">{meta}</p>
    </div>
  );
};
