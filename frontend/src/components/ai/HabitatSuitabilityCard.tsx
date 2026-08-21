import React from 'react';
import { HabitatSuitabilityResult } from '../../types/ml';
import { Compass, Sparkles, Sliders, CheckCircle2 } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const HabitatSuitabilityCard: React.FC<{ suitability: HabitatSuitabilityResult }> = ({
  suitability
}) => {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-marine-800 space-y-4 hover:border-ocean-teal/40 transition-all">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-sm font-semibold text-white">{suitability.commonName}</h4>
          <p className="text-xs italic text-slate-400 font-serif">{suitability.speciesName}</p>
        </div>
        <Badge variant="teal" size="sm">
          {(suitability.suitabilityIndex * 100).toFixed(0)}% Habitat Match
        </Badge>
      </div>

      {/* Target Region & Environmental Envelope */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2 rounded bg-marine-950/80 border border-marine-850">
          <span className="text-[10px] text-slate-400 block font-sans">Optimal Depth Window:</span>
          <span className="text-white font-semibold">
            {suitability.optimalDepthRangeMeters[0]}m - {suitability.optimalDepthRangeMeters[1]}m
          </span>
        </div>
        <div className="p-2 rounded bg-marine-950/80 border border-marine-850">
          <span className="text-[10px] text-slate-400 block font-sans">Optimal Thermal Window:</span>
          <span className="text-white font-semibold">
            {suitability.optimalTemperatureRangeCelsius[0]}°C - {suitability.optimalTemperatureRangeCelsius[1]}°C
          </span>
        </div>
      </div>

      {/* Environmental Drivers Table */}
      <div className="space-y-1.5 pt-1">
        <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
          Environmental Drivers & Limits
        </span>
        {suitability.environmentalDrivers.map((d, idx) => (
          <div key={idx} className="flex items-center justify-between text-xs p-2 rounded bg-marine-900/60 border border-marine-850">
            <span className="text-slate-300 font-medium">{d.driver}</span>
            <div className="flex items-center gap-3 font-mono text-[11px]">
              <span className="text-ocean-cyan">{d.currentValue}</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400">Opt: {d.optimalRange}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
