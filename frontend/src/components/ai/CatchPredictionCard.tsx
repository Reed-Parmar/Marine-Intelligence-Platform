import React from 'react';
import { CatchForecastResult } from '../../types/ml';
import { TrendingUp, TrendingDown, Minus, Calendar, Fish, Sparkles, Activity, Layers } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface CatchPredictionCardProps {
  forecast: CatchForecastResult;
  onSimulate?: (species: string) => void;
}

export const CatchPredictionCard: React.FC<CatchPredictionCardProps> = ({ forecast, onSimulate }) => {
  const getTrendConfig = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return {
          icon: <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />,
          badgeVariant: 'teal' as const,
          label: 'Increasing Yield',
          textColor: 'text-emerald-400'
        };
      case 'declining':
        return {
          icon: <TrendingDown className="w-3.5 h-3.5 text-ocean-coral" />,
          badgeVariant: 'coral' as const,
          label: 'Declining Yield',
          textColor: 'text-ocean-coral'
        };
      default:
        return {
          icon: <Minus className="w-3.5 h-3.5 text-ocean-amber" />,
          badgeVariant: 'amber' as const,
          label: 'Stable Yield',
          textColor: 'text-ocean-amber'
        };
    }
  };

  const trendConfig = getTrendConfig(forecast.trendDirection);
  const percentDelta = Math.round(((forecast.predictedCatchTons - forecast.historicalAverageTons) / forecast.historicalAverageTons) * 100);

  // Calculate relative CI span for mini visualization
  const [ciLow, ciHigh] = forecast.confidenceInterval95;
  const ciRange = ciHigh - ciLow;
  const posInCi = Math.min(Math.max(((forecast.predictedCatchTons - ciLow) / (ciRange || 1)) * 100, 10), 90);

  return (
    <div className="glass-panel rounded-2xl p-5 border border-marine-800 space-y-4 hover:border-ocean-cyan/50 hover:shadow-lg hover:shadow-ocean-cyan/5 transition-all duration-300 group flex flex-col justify-between">
      <div className="space-y-3">
        {/* Card Header */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-1.5 text-xs text-ocean-cyan font-mono">
              <Calendar className="w-3.5 h-3.5" />
              <span>{forecast.forecastPeriod}</span>
            </div>
            <h4 className="text-sm font-semibold text-white mt-1 flex items-center gap-1.5 group-hover:text-ocean-cyan transition-colors">
              <Fish className="w-4 h-4 text-ocean-cyan shrink-0" />
              <span>{forecast.targetSpecies}</span>
            </h4>
          </div>

          <Badge variant={trendConfig.badgeVariant} size="sm" className="shrink-0 flex items-center gap-1">
            {trendConfig.icon}
            <span>{trendConfig.label}</span>
          </Badge>
        </div>

        {/* Prediction Metrics Box */}
        <div className="p-4 rounded-xl bg-marine-950/80 border border-marine-800/80 space-y-3">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Predicted Landings (MBLF-Net)</span>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="text-2xl font-mono font-bold text-white tracking-tight">
                  {forecast.predictedCatchTons.toLocaleString()}
                </span>
                <span className="text-xs text-ocean-cyan font-mono">Tons</span>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">vs Baseline</span>
              <span className={`text-xs font-mono font-bold ${percentDelta >= 0 ? 'text-emerald-400' : 'text-ocean-coral'}`}>
                {percentDelta >= 0 ? `+${percentDelta}%` : `${percentDelta}%`}
              </span>
              <span className="text-[10px] text-slate-500 block font-mono">({forecast.historicalAverageTons.toLocaleString()} T hist.)</span>
            </div>
          </div>

          {/* 95% Confidence Interval Bar */}
          <div className="space-y-1.5 pt-1 border-t border-marine-850">
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
              <span>95% CI Lower: <strong className="text-slate-300 font-normal">{ciLow.toLocaleString()} T</strong></span>
              <span>Upper: <strong className="text-slate-300 font-normal">{ciHigh.toLocaleString()} T</strong></span>
            </div>
            <div className="h-1.5 w-full bg-marine-900 rounded-full overflow-hidden relative">
              <div
                className="h-full bg-gradient-to-r from-ocean-teal via-ocean-cyan to-ocean-blue rounded-full"
                style={{ width: '100%' }}
              />
              <div
                className="absolute top-0 bottom-0 w-2 bg-white rounded-full shadow-glow -translate-x-1"
                style={{ left: `${posInCi}%` }}
                title="Predicted Mean Point"
              />
            </div>
          </div>
        </div>

        {/* Model Driver Feature Tags */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Activity className="w-3 h-3 text-ocean-cyan" />
              MBLF-Net Driver Features
            </span>
            <span className="text-[9px] font-mono text-slate-500">XGBoost</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {['Historical_CPUE', 'Monsoon_Index', 'SST_Lag30', 'Fishing_Effort_Hours'].map((feature, idx) => (
              <span
                key={idx}
                className="px-1.5 py-0.5 rounded bg-marine-900/90 border border-marine-800 text-[9px] font-mono text-slate-300 hover:border-ocean-cyan/40 transition-colors"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>

        {/* Advisory / Explanation */}
        <p className="text-xs text-slate-300 leading-relaxed border-t border-marine-850 pt-3">
          {forecast.modelExplanation}
        </p>
      </div>

      {onSimulate && (
        <div className="pt-3 border-t border-marine-850 flex justify-end">
          <button
            onClick={() => onSimulate(forecast.targetSpecies)}
            className="text-xs text-ocean-cyan hover:text-white flex items-center gap-1.5 transition-colors font-medium cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Simulate Catch Prediction</span>
          </button>
        </div>
      )}
    </div>
  );
};
