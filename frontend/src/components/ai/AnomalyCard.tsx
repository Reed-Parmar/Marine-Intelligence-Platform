import React from 'react';
import { AnomalyDetectionResult } from '../../types/ml';
import { AlertTriangle, MapPin, Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const AnomalyCard: React.FC<{ anomaly: AnomalyDetectionResult }> = ({ anomaly }) => {
  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'Extreme':
      case 'Severe':
        return <Badge variant="coral" size="sm" dot>{sev} Severity</Badge>;
      case 'High':
        return <Badge variant="amber" size="sm">{sev} Severity</Badge>;
      default:
        return <Badge variant="cyan" size="sm">{sev} Severity</Badge>;
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-marine-800 space-y-4 hover:border-ocean-coral/40 transition-all">
      {/* Top Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-ocean-coral/20 text-ocean-coral">
              <AlertTriangle className="w-4 h-4" />
            </span>
            <h4 className="text-sm font-semibold text-white">{anomaly.anomalyType}</h4>
          </div>
          <p className="text-xs text-slate-300 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-ocean-cyan" />
            {anomaly.region}
          </p>
        </div>
        {getSeverityBadge(anomaly.severity)}
      </div>

      {/* Baseline vs Current Values */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded-lg bg-marine-950/80 border border-marine-850">
          <span className="text-[10px] text-slate-400 block font-sans">Historical Baseline:</span>
          <span className="text-slate-300">{anomaly.baselineExpectedValue}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-marine-950/80 border border-ocean-coral/30">
          <span className="text-[10px] text-slate-400 block font-sans">Observed Sensor Cast:</span>
          <span className="text-ocean-coral font-bold">{anomaly.observedCurrentValue}</span>
        </div>
      </div>

      {/* Feature Importance Weights */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
          Contributing Driver Features (SHAP Weights)
        </span>
        <div className="space-y-1.5">
          {anomaly.contributingFeatures.map((feat, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs p-1.5 rounded bg-marine-900/60 border border-marine-850">
              <span className="text-slate-300">{feat.feature}</span>
              <div className="flex items-center gap-1 font-mono">
                {feat.impactDirection === 'positive' ? (
                  <ArrowUpRight className="w-3.5 h-3.5 text-ocean-coral" />
                ) : (
                  <ArrowDownRight className="w-3.5 h-3.5 text-ocean-cyan" />
                )}
                <span className="text-white font-bold">{(feat.importanceWeight * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Mitigation Advice */}
      <div className="p-3 rounded-xl bg-marine-900/40 border border-marine-800 text-xs text-slate-300 leading-relaxed">
        <span className="font-semibold text-white">Actionable Scientific Advisory: </span>
        {anomaly.mitigationAdvice}
      </div>
    </div>
  );
};
