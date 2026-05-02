import React from 'react';

interface ChartBoxProps {
  height?: number;
  children: React.ReactNode;
}

export const ChartBox: React.FC<ChartBoxProps> = ({ height = 200, children }) => {
  return <div style={{ height }}>{children}</div>;
};
