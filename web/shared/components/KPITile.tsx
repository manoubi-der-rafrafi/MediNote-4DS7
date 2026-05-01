import React from 'react';
import { theme } from '../../theme';

interface KPITileProps {
  value: string | number;
  label: string;
  delta?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: keyof typeof theme.colors;
}

export const KPITile: React.FC<KPITileProps> = ({
  value,
  label,
  delta,
  trend = 'neutral',
  color = 'blue',
}) => {
  const colorValue = (theme.colors as any)[color];
  const trendColors = {
    up: theme.colors.green,
    down: theme.colors.red,
    neutral: theme.colors.txt3,
  };

  return (
    <div
      style={{
        background: theme.colors.s1,
        border: `1px solid ${theme.colors.b1}`,
        borderRadius: theme.radius.r2,
        padding: '12px 14px',
        transition: 'border-color 0.12s',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = theme.colors.b2)}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = theme.colors.b1)}
    >
      <div
        style={{
          fontFamily: theme.fonts.heading,
          fontSize: '24px',
          fontWeight: 800,
          letterSpacing: '-0.04em',
          lineHeight: 1,
          color: colorValue,
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: '10px', color: theme.colors.txt2, marginTop: '4px', fontWeight: 500 }}>
        {label}
      </div>
      {delta && (
        <div
          style={{
            fontSize: '10px',
            fontWeight: 600,
            marginTop: '5px',
            color: trendColors[trend],
          }}
        >
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {delta}
        </div>
      )}
    </div>
  );
};
