import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export interface BarSeriesConfig {
  key: string;
  name: string;
  color: string;
}

export interface DistributionBarChartProps {
  data: any[];
  series: BarSeriesConfig[];
  xAxisKey: string;
  height?: number;
}

export const DistributionBarChart: React.FC<DistributionBarChartProps> = ({
  data,
  series,
  xAxisKey,
  height = 280
}) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1c2f5d" opacity={0.5} />
          <XAxis
            dataKey={xAxisKey}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 18, 36, 0.95)',
              border: '1px solid #00f0ff',
              borderRadius: '8px',
              fontSize: '12px'
            }}
          />
          <Legend wrapperStyle={{ paddingTop: 8, fontSize: '12px' }} />
          {series.map((s) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.name}
              fill={s.color}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
