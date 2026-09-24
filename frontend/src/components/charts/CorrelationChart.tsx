import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Scatter,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { CorrelationDataPoint } from '../../types/analysis';

export interface CorrelationChartProps {
  scatterPoints: CorrelationDataPoint[];
  regressionLine: {
    xMin: number;
    xMax: number;
    yAtMin: number;
    yAtMax: number;
  };
  xLabel: string;
  yLabel: string;
  height?: number;
}

export const CorrelationChart: React.FC<CorrelationChartProps> = ({
  scatterPoints,
  regressionLine,
  xLabel,
  yLabel,
  height = 320
}) => {
  // Format regression line for ComposedChart
  const lineData = [
    { x: regressionLine.xMin, lineY: regressionLine.yAtMin },
    { x: regressionLine.xMax, lineY: regressionLine.yAtMax }
  ];

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart margin={{ top: 15, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1c2f5d" opacity={0.5} />
          <XAxis
            type="number"
            dataKey="x"
            name={xLabel}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            label={{ value: xLabel, position: 'bottom', offset: 5, fill: '#94a3b8', fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yLabel}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{
              backgroundColor: 'rgba(10, 18, 36, 0.95)',
              border: '1px solid #00f0ff',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#f8fafc'
            }}
          />
          {/* Scatter Points */}
          <Scatter
            name="Observation Samples"
            data={scatterPoints}
            fill="#00f0ff"
            line={false}
            shape="circle"
          />
          {/* Linear OLS Regression Line */}
          <Line
            data={lineData}
            dataKey="lineY"
            type="linear"
            name="OLS Regression Line"
            stroke="#06d6a0"
            strokeWidth={2.5}
            dot={false}
            activeDot={false}
            legendType="none"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
