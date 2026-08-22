import React from 'react';
import { AnalysisResultData } from '../../types/analysis';
import { Calculator, CheckCircle2, TrendingUp, HelpCircle } from 'lucide-react';

export const StatisticalSummary: React.FC<{ statistics: AnalysisResultData['statistics'] }> = ({
  statistics
}) => {
  const getPValueInterpretation = (p: number | null | undefined) => {
    if (p === null || p === undefined) return { label: 'p-value: N/A', color: 'text-slate-400' };
    if (p < 0.001) return { label: 'p < 0.001 (Highly Significant)', color: 'text-emerald-400' };
    if (p < 0.05) return { label: 'p < 0.05 (Statistically Significant)', color: 'text-ocean-cyan' };
    return { label: 'p >= 0.05 (Non-Significant)', color: 'text-ocean-amber' };
  };

  const pInterp = getPValueInterpretation(statistics.pValue);

  return (
    <div className="glass-panel rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-marine-800 pb-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-white">
          <Calculator className="w-4 h-4 text-ocean-cyan" />
          <span>Regression & Correlation Statistics</span>
        </div>
        <span className={`text-[11px] font-mono font-semibold ${pInterp.color}`}>
          {pInterp.label}
        </span>
      </div>

      {/* Grid of Key Statistical Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800">
          <span className="text-[10px] text-slate-400 block font-sans">Pearson Correlation (r):</span>
          <span className="text-base font-mono font-bold text-ocean-cyan">
            {statistics.pearsonR !== null && statistics.pearsonR !== undefined
              ? (statistics.pearsonR > 0 ? `+${statistics.pearsonR}` : statistics.pearsonR)
              : '—'}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800">
          <span className="text-[10px] text-slate-400 block font-sans">Coeff of Determination (R²):</span>
          <span className="text-base font-mono font-bold text-ocean-teal">
            {statistics.rSquared !== null && statistics.rSquared !== undefined
              ? `${(statistics.rSquared * 100).toFixed(1)}%`
              : '—'}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800">
          <span className="text-[10px] text-slate-400 block font-sans">Sample Count (N):</span>
          <span className="text-base font-mono font-bold text-white">
            {statistics.sampleSize ?? '—'}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800">
          <span className="text-[10px] text-slate-400 block font-sans">Regression Slope (m):</span>
          <span className="text-base font-mono font-bold text-ocean-amber">
            {statistics.slope !== null && statistics.slope !== undefined ? statistics.slope.toFixed(2) : '—'}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
        <span>Intercept (c): {statistics.intercept !== null && statistics.intercept !== undefined ? statistics.intercept.toFixed(2) : '—'}</span>
        <span>Std Error (SE): {statistics.standardError !== null && statistics.standardError !== undefined ? statistics.standardError.toFixed(2) : '—'}</span>
        <span>F-Statistic: {statistics.fStatistic !== null && statistics.fStatistic !== undefined ? statistics.fStatistic.toFixed(1) : '—'}</span>
      </div>
    </div>
  );
};
