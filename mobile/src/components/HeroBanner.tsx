import React from 'react';

interface HeroBannerProps {
  label: string;
  bigValue: string;
  subtitle: string;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({ label, bigValue, subtitle }) => {
  return (
    <div
      className="rounded-lg p-4 mb-3"
      style={{
        background: 'linear-gradient(135deg, var(--brand), var(--brand-2))',
        borderRadius: 'var(--radius)',
      }}
    >
      <p className="text-[10.5px] uppercase tracking-wider text-white/85">{label}</p>
      <p className="text-[28px] font-light text-white mt-1">{bigValue}</p>
      <p className="text-[12px] text-white/88 mt-1">{subtitle}</p>
    </div>
  );
};
