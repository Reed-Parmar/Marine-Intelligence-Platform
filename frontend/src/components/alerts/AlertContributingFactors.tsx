import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export interface AlertContributingFactorsProps {
  factors: {
    factor: string;
    direction: 'up' | 'down' | 'neutral';
    value: string;
  }[];
}

export const AlertContributingFactors: React.FC<AlertContributingFactorsProps> = ({ factors }) => {
  return (
    <div className="space-y-1.5">
      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
        Contributing Ecological & Physical Drivers
      </span>
      <div className="flex flex-wrap gap-2">
        {factors.map((f, idx) => {
          const isUp = f.direction === 'up';
          const isDown = f.direction === 'down';
          return (
            <div
              key={idx}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-marine-900 border border-marine-800 text-xs font-mono"
            >
              {isUp && <ArrowUp className="w-3.5 h-3.5 text-ocean-coral" />}
              {isDown && <ArrowDown className="w-3.5 h-3.5 text-ocean-cyan" />}
              {!isUp && !isDown && <Minus className="w-3.5 h-3.5 text-slate-400" />}
              <span className="text-slate-300 font-sans">{f.factor}:</span>
              <span className="text-white font-bold">{f.value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
