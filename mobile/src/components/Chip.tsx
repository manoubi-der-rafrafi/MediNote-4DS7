import React from 'react';

interface ChipProps {
  label: string;
  variant?: 'pos' | 'neg' | 'warn' | 'br' | 'default';
}

export const Chip: React.FC<ChipProps> = ({ label, variant = 'default' }) => {
  const variants: Record<string, { bg: string; color: string }> = {
    pos: { bg: 'rgba(74, 124, 89, 0.12)', color: 'var(--pos)' },
    neg: { bg: 'rgba(185, 74, 72, 0.12)', color: 'var(--neg)' },
    warn: { bg: 'rgba(184, 134, 11, 0.14)', color: 'var(--warn)' },
    br: { bg: 'var(--brand-soft)', color: 'var(--brand)' },
    default: { bg: '#F4F3EE', color: 'var(--muted)' },
  };

  const style = variants[variant];

  return (
    <span
      className="inline-block text-[10.5px] font-medium px-2 py-0.5"
      style={{ backgroundColor: style.bg, color: style.color, borderRadius: 999 }}
    >
      {label}
    </span>
  );
};
