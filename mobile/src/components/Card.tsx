import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, subtitle, children, className = '' }) => {
  return (
    <div
      className={`p-3.5 mb-3 ${className}`}
      style={{
        backgroundColor: 'var(--card)',
        border: '0.5px solid var(--border)',
        borderRadius: 'var(--radius)',
      }}
    >
      {title && <p className="text-[13px] font-medium text-[var(--text)]">{title}</p>}
      {subtitle && <p className="text-[11px] text-[var(--muted)] mt-0.5 mb-2.5">{subtitle}</p>}
      {children}
    </div>
  );
};
