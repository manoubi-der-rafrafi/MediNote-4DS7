import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ForecastData {
  month: string;
  pessimiste: number;
  realiste: number;
  optimiste: number;
}

interface ForecastChartProps {
  data: ForecastData[];
  title?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="bg-s2 border border-bd rounded p-3">
      <p className="text-xs font-semibold text-gray-300">{payload[0]?.payload.month}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-xs">
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
};

export const ForecastChart: React.FC<ForecastChartProps> = ({ data, title }) => {
  return (
    <div className="w-full">
      {title && <h3 className="text-sm font-semibold mb-2">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorPessimiste" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F87171" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#F87171" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorRealiste" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4F8EF7" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#4F8EF7" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorOptimiste" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34D399" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#2A2A35"
            vertical={false}
          />
          <XAxis
            dataKey="month"
            stroke="#A0A0B0"
            style={{ fontSize: '12px' }}
          />
          <YAxis stroke="#A0A0B0" style={{ fontSize: '12px' }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          <Area
            type="monotone"
            dataKey="pessimiste"
            stroke="#F87171"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPessimiste)"
          />
          <Area
            type="monotone"
            dataKey="realiste"
            stroke="#4F8EF7"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorRealiste)"
          />
          <Area
            type="monotone"
            dataKey="optimiste"
            stroke="#34D399"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorOptimiste)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
