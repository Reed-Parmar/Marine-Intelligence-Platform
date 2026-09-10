import React from 'react';
import { AlertSeverity } from '../../types/alert';
import { AlertTriangle, AlertOctagon, Info, ShieldAlert } from 'lucide-react';

export const AlertSeverityBadge: React.FC<{ severity: AlertSeverity }> = ({ severity }) => {
  const configs = {
    critical: {
      bg: 'bg-rose-950/60 border-rose-500/50 text-rose-300',
      icon: <AlertOctagon className="w-3.5 h-3.5 text-ocean-coral" />,
      dot: 'bg-ocean-coral animate-ping',
      label: 'Critical Hazard'
    },
    warning: {
      bg: 'bg-amber-950/60 border-amber-500/50 text-amber-300',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-ocean-amber" />,
      dot: 'bg-ocean-amber',
      label: 'Warning'
    },
    advisory: {
      bg: 'bg-cyan-950/60 border-cyan-500/50 text-cyan-300',
      icon: <ShieldAlert className="w-3.5 h-3.5 text-ocean-cyan" />,
      dot: 'bg-ocean-cyan',
      label: 'Advisory'
    },
    info: {
      bg: 'bg-slate-900 border-slate-700 text-slate-300',
      icon: <Info className="w-3.5 h-3.5 text-slate-400" />,
      dot: 'bg-slate-400',
      label: 'Notice'
    }
  };

  const c = configs[severity] || configs.info;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${c.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      <span>{c.label}</span>
    </span>
  );
};
