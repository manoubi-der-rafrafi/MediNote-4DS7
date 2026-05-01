import React from 'react';

type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'tier-a'
  | 'tier-b'
  | 'tier-c'
  | 'tier-d';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-s2 text-gray-300 border border-bd',
  success: 'bg-green/15 text-green border border-green/30',
  warning: 'bg-gold/15 text-gold border border-gold/30',
  danger: 'bg-red/15 text-red border border-red/30',
  info: 'bg-blue/15 text-blue border border-blue/30',
  'tier-a': 'bg-teal/15 text-teal border border-teal/30',
  'tier-b': 'bg-blue/15 text-blue border border-blue/30',
  'tier-c': 'bg-orange/15 text-orange border border-orange/30',
  'tier-d': 'bg-red/15 text-red border border-red/30',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  className = '',
}) => {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
