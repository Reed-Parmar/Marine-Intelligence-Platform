import React from 'react';
import { CatchForecastResult } from '../../types/ml';
import { TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const PredictionCard: React.FC<{ forecast: CatchForecastResult }> = ({ forecast }) => {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-ocean-coral" />;
      default:
        return <Minus className="w-4 h-4 text-ocean-amber" />;
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-marine-800 space-y-4 hover:border-ocean-cyan/40 transition-all">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5 text-xs text-ocean-cyan font-mono">
            <Calendar className="w-3.5 h-3.5" />
            <span>{forecast.forecastPeriod}</span>
          </div>
          <h4 className="text-sm font-semibold text-white mt-1">{forecast.targetSpecies}</h4>
        </div>
        <div className="flex items-center gap-1 p-1.5 rounded-lg bg-marine-900 border border-marine-800">
          {getTrendIcon(forecast.trendDirection)}
          <span className="text-xs capitalize text-slate-300 font-medium">{forecast.trendDirection}</span>
        </div>
      </div>

      {/* Projection Metric */}
      <div className="p-4 rounded-xl bg-marine-900/80 border border-marine-800 flex items-center justify-between">
        <div>
          <span className="text-[10px] text-slate-400 block font-sans">Predicted Stock Biomass:</span>
          <span className="text-xl font-mono font-bold text-ocean-cyan">
            {forecast.predictedCatchTons.toLocaleString()} <span className="text-xs font-normal">Tons</span>
          </span>
        </div>
        <div className="text-right text-xs font-mono">
          <span className="text-[10px] text-slate-400 block font-sans">95% CI Window:</span>
          <span className="text-slate-300">
            {forecast.confidenceInterval95[0].toLocaleString()} - {forecast.confidenceInterval95[1].toLocaleString()} T
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed border-t border-marine-850 pt-3">
        {forecast.modelExplanation}
      </p>
    </div>
  );
};
