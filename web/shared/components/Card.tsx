import React from 'react';
import { theme } from '../../theme';

interface CardProps {
  children: React.ReactNode;
  header?:  string;
  headerAction?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, header, headerAction }) => {
  return (
    <div
      style={{
        background: theme.colors.s1,
        border: `1px solid ${theme.colors.b1}`,
        borderRadius: theme.radius.r2,
        overflow: 'hidden',
      }}
    >
      {header && (
        <div
          style={{
            padding: '11px 14px',
            borderBottom: `1px solid ${theme.colors.b1}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              color: theme.colors.txt,
            }}
          >
            {header}
          </div>
          {headerAction && (
            <div style={{ fontSize: '10px', color: theme.colors.blue, cursor: 'pointer' }}>
              {headerAction}
            </div>
          )}
        </div>
      )}
      <div style={{ padding: '14px' }}>{children}</div>
    </div>
  );
};
