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
import { CTDProfilePoint } from '../../types/ocean';

export interface DepthProfileChartProps {
  data: CTDProfilePoint[];
  height?: number;
}

export const DepthProfileChart: React.FC<DepthProfileChartProps> = ({
  data,
  height = 320
}) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1c2f5d" opacity={0.5} />
          {/* Depth on Y-Axis (Inverted: 0m at top, 500m at bottom) */}
          <YAxis
            type="number"
            dataKey="depth"
            reversed
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            unit="m"
            label={{ value: 'Depth (meters)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
          />
          <XAxis
            type="number"
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 18, 36, 0.95)',
              border: '1px solid #00f0ff',
              borderRadius: '8px',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
              fontSize: '12px'
            }}
          />
          <Legend wrapperStyle={{ paddingTop: 8, fontSize: '12px' }} />
          <Line
            type="monotone"
            dataKey="temperature"
            name="Temperature (°C)"
            stroke="#00f0ff"
            strokeWidth={2.5}
            dot={{ r: 2 }}
          />
          <Line
            type="monotone"
            dataKey="salinity"
            name="Salinity (PSU)"
            stroke="#06d6a0"
            strokeWidth={2}
            dot={{ r: 2 }}
          />
          <Line
            type="monotone"
            dataKey="dissolvedOxygen"
            name="Dissolved Oxygen (mg/L)"
            stroke="#ffb703"
            strokeWidth={2}
            dot={{ r: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
