import React from 'react';

interface ThemeTagProps {
  label: string;
  count: number;
}

export const ThemeTag: React.FC<ThemeTagProps> = ({ label, count }) => {
  return (
    <span className="inline-block bg-brand-soft px-3 py-1 rounded-full text-xs mr-2 mb-2">
      {label}·<span className="font-bold">{count}</span>
    </span>
  );
};
