import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Clock } from 'lucide-react';

export const QualityScoreBadge: React.FC<{ score: number | null; status?: string; size?: 'sm' | 'md' }> = ({
  score,
  status,
  size = 'md'
}) => {
  if (score === null || score === undefined) {
    const pendingStyle = 'bg-slate-700/30 border-slate-600/30 text-slate-400';
    if (size === 'sm') {
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-mono font-semibold ${pendingStyle}`}>
          QC Pending
        </span>
      );
    }
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${pendingStyle}`}>
        <Clock className="w-3.5 h-3.5" />
        <span className="text-xs font-sans font-medium">QC Pending</span>
      </div>
    );
  }

  const getBadgeConfig = () => {
    if (score >= 90) {
      return {
        bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
        icon: <ShieldCheck className="w-3.5 h-3.5" />,
        label: 'Excellent Quality'
      };
    }
    if (score >= 75) {
      return {
        bg: 'bg-ocean-cyan/15 border-ocean-cyan/30 text-ocean-cyan',
        icon: <ShieldCheck className="w-3.5 h-3.5" />,
        label: 'Good Quality'
      };
    }
    if (score >= 50) {
      return {
        bg: 'bg-ocean-amber/15 border-ocean-amber/30 text-ocean-amber',
        icon: <AlertTriangle className="w-3.5 h-3.5" />,
        label: 'Quality Warning'
      };
    }
    return {
      bg: 'bg-ocean-coral/15 border-ocean-coral/30 text-ocean-coral',
      icon: <AlertOctagon className="w-3.5 h-3.5" />,
      label: 'Critical QC Issues'
    };
  };

  const config = getBadgeConfig();

  if (size === 'sm') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-mono font-semibold ${config.bg}`}>
        {score}%
      </span>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${config.bg}`}>
      {config.icon}
      <div className="flex items-center gap-1.5 font-mono text-xs">
        <span className="font-bold">{score}%</span>
        <span className="text-slate-400">|</span>
        <span className="text-[11px] font-sans font-medium">{config.label}</span>
      </div>
    </div>
  );
};
