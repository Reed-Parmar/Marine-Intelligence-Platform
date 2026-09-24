import React from 'react';
import { MarineAlert } from '../../types/alert';
import { AlertSeverityBadge } from './AlertSeverityBadge';
import { AlertContributingFactors } from './AlertContributingFactors';
import { MapPin, Clock, CheckCircle2, ShieldCheck } from 'lucide-react';
import { Button } from '../ui/Button';

export interface AlertCardProps {
  alert: MarineAlert;
  onAcknowledge?: (id: string) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, onAcknowledge }) => {
  const getBorderColor = () => {
    switch (alert.severity) {
      case 'critical':
        return 'border-ocean-coral/40 bg-rose-950/20';
      case 'warning':
        return 'border-ocean-amber/40 bg-amber-950/20';
      case 'advisory':
        return 'border-ocean-cyan/40 bg-cyan-950/20';
      default:
        return 'border-marine-800 bg-marine-900/60';
    }
  };

  return (
    <div className={`glass-panel rounded-2xl p-6 border space-y-5 transition-all shadow-xl ${getBorderColor()}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-marine-800/80 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h4 className="text-base font-semibold text-white">{alert.title}</h4>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-ocean-cyan" />
              {alert.region}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 font-mono">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-center">
          <AlertSeverityBadge severity={alert.severity} />
          <span className="text-xs font-mono font-bold text-ocean-cyan px-2.5 py-1 rounded bg-marine-900 border border-marine-800">
            {alert.confidencePercent}% Confidence
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-200 leading-relaxed">{alert.description}</p>

      {/* Contributing Factors */}
      <AlertContributingFactors factors={alert.contributingFactors} />

      {/* Affected Sectors */}
      <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
        <span className="text-slate-400">Affected Domains/Stocks:</span>
        {alert.affectedSpeciesOrIndustries.map((sec, idx) => (
          <span key={idx} className="px-2 py-0.5 rounded bg-marine-900 border border-marine-800 text-[11px] text-slate-300">
            {sec}
          </span>
        ))}
      </div>

      {/* Recommended Action & Acknowledge Footer */}
      <div className="p-3.5 rounded-xl bg-marine-950/70 border border-marine-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="text-xs">
          <span className="font-semibold text-white">Recommended Policy / Fleet Action: </span>
          <span className="text-slate-300">{alert.recommendedAction}</span>
        </div>

        {alert.isAcknowledged ? (
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium whitespace-nowrap self-end sm:self-center">
            <CheckCircle2 className="w-4 h-4" />
            <span>Acknowledged</span>
          </div>
        ) : onAcknowledge ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAcknowledge(alert.id)}
            leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-ocean-cyan" />}
            className="self-end sm:self-center"
          >
            Acknowledge Alert
          </Button>
        ) : null}
      </div>
    </div>
  );
};
