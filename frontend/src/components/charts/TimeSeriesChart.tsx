import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export interface TimeSeriesPoint {
  date: string;
  [key: string]: any;
}

export interface TimeSeriesSeries {
  key: string;
  name: string;
  color: string;
  unit?: string;
}

export interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  series: TimeSeriesSeries[];
  height?: number;
  xAxisKey?: string;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  series,
  height = 280,
  xAxisKey = 'date'
}) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1c2f5d" opacity={0.5} />
          <XAxis
            dataKey={xAxisKey}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#334155' }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#334155' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 18, 36, 0.95)',
              border: '1px solid #00f0ff',
              borderRadius: '8px',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
              fontSize: '12px',
              color: '#f8fafc'
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: 10, fontSize: '12px', color: '#cbd5e1' }}
          />
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              dot={{ r: 3, fill: s.color }}
              activeDot={{ r: 5, stroke: '#ffffff', strokeWidth: 1 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
