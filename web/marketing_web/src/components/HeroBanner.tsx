import React from 'react';

interface HeroBannerProps {
  label: string;
  value: string;
  description: string;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({ label, value, description }) => {
  return (
    <div className="rounded-lg p-6 mb-6 text-white" style={{ background: 'linear-gradient(135deg, #D4537E 0%, #72243E 100%)' }}>
      <div className="grid grid-cols-2 gap-8">
        <div>
          <div className="text-sm font-semibold opacity-90 mb-2">{label}</div>
          <div className="text-4xl font-bold mb-2">{value}</div>
          <div className="inline-block bg-white/20 px-2 py-1 rounded text-xs font-semibold">ML Model</div>
        </div>
        <div className="text-right text-sm leading-relaxed opacity-90">{description}</div>
      </div>
    </div>
  );
};
