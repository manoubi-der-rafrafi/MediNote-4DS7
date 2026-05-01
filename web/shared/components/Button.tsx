import React from 'react';
import { theme } from '../../theme';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', size = 'md', onClick }) => {
  const variants = {
    primary: {
      bg: theme.colors.blue,
      text: '#fff',
      hover: theme.colors.blueDark,
    },
    secondary: {
      bg: theme.colors.s3,
      text: theme.colors.txt2,
      hover: theme.colors.b2,
    },
  };

  const sizes = {
    sm: { padding: '4px 10px', fontSize: '9px' },
    md: { padding: '9px', fontSize: '11px' },
    lg: { padding: '12px 16px', fontSize: '12px' },
  };

  const style = variants[variant];
  const size_style = sizes[size];

  return (
    <button
      onClick={onClick}
      style={{
        background: style.bg,
        color: style.text,
        border: 'none',
        borderRadius: theme.radius.r,
        padding: size_style.padding,
        fontSize: size_style.fontSize,
        fontWeight: 700,
        cursor: 'pointer',
        transition: 'opacity 0.12s',
        fontFamily: theme.fonts.body,
      }}
      onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
      onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
    >
      {children}
    </button>
  );
};
