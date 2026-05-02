import React from 'react';

interface AvatarProps {
  initials: string;
  size?: number;
}

export const Avatar: React.FC<AvatarProps> = ({ initials, size = 34 }) => {
  return (
    <div
      className="flex items-center justify-center font-semibold"
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: 'var(--brand-soft)',
        color: 'var(--brand)',
        fontSize: size * 0.35,
      }}
    >
      {initials}
    </div>
  );
};
