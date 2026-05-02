import React from 'react';

interface TierBadgeProps {
  tier: 'A' | 'B' | 'C' | 'D';
}

export const TierBadge: React.FC<TierBadgeProps> = ({ tier }) => {
  const tierStyles: Record<string, { bg: string; color: string }> = {
    A: { bg: 'rgba(74, 124, 89, 0.12)', color: 'var(--pos)' },
    B: { bg: 'var(--brand-soft)', color: 'var(--brand)' },
    C: { bg: 'rgba(184, 134, 11, 0.14)', color: 'var(--warn)' },
    D: { bg: 'rgba(185, 74, 72, 0.12)', color: 'var(--neg)' },
  };

  const style = tierStyles[tier];

  return (
    <span
      className="inline-block text-[10.5px] font-semibold px-2 py-0.5 uppercase"
      style={{ backgroundColor: style.bg, color: style.color, borderRadius: 999 }}
    >
      Tier {tier}
    </span>
  );
};
