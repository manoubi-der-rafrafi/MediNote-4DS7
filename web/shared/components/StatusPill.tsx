import React from 'react';
import { theme } from '../../theme';

interface StatusPillProps {
  status: 'green' | 'amber' | 'red' | 'blue' | 'purple';
  label: string;
}

const statusStyles = {
  green: { bg: 'rgba(61, 214, 140, 0.08)', text: '#3DD68C', border: 'rgba(61, 214, 140, 0.22)' },
  amber: { bg: 'rgba(245, 166, 35, 0.08)', text: '#F5A623', border: 'rgba(245, 166, 35, 0.22)' },
  red: { bg: 'rgba(240, 101, 101, 0.08)', text: '#F06565', border: 'rgba(240, 101, 101, 0.22)' },
  blue: { bg: 'rgba(91, 141, 246, 0.1)', text: '#5B8DF6', border: 'rgba(91, 141, 246, 0.22)' },
  purple: { bg: 'rgba(155, 127, 255, 0.1)', text: '#9B7FFF', border: 'rgba(155, 127, 255, 0.22)' },
};

export const StatusPill: React.FC<StatusPillProps> = ({ status, label }) => {
  const style = statusStyles[status];
  return (
    <span
      style={{
        fontSize: '9px',
        fontWeight: 700,
        padding: '2px 7px',
        borderRadius: '4px',
        background: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        letterSpacing: '0.02em',
        display: 'inline-block',
      }}
    >
      {label}
    </span>
  );
};
