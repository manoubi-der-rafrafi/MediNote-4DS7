import React from 'react';

interface RingChartProps {
  progress: number;
  color: string;
  size?: number;
  label: string;
  sublabel?: string;
}

export const RingChart: React.FC<RingChartProps> = ({
  progress,
  color,
  size = 100,
  label,
  sublabel,
}) => {
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const colorMap: Record<string, string> = {
    teal: '#2DD4BF',
    blue: '#4F8EF7',
    gold: '#FBBF24',
    green: '#34D399',
    red: '#F87171',
    purple: '#A78BFA',
    orange: '#FB923C',
  };

  const ringColor = colorMap[color] || colorMap.marketing;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="mb-3">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#2A2A35"
          strokeWidth="8"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{ transform: `rotate(-90deg)`, transformOrigin: '50% 50%' }}
        />
        <text
          x={size / 2}
          y={size / 2}
          textAnchor="middle"
          dy="0.3em"
          className="text-lg font-bold"
          fill="white"
        >
          {progress}%
        </text>
      </svg>
      <p className="text-sm font-semibold text-center">{label}</p>
      {sublabel && <p className="text-xs text-gray-400 text-center mt-1">{sublabel}</p>}
    </div>
  );
};
