import React, { useEffect, useState } from 'react';
import { alertsService } from '../../services/alerts';
import { MarineAlert, AlertSummaryMetrics, AlertSeverity } from '../../types/alert';
import { AlertCard } from '../../components/alerts/AlertCard';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../context/ToastContext';
import { AlertTriangle, ShieldAlert, AlertOctagon, Filter, CheckCircle2 } from 'lucide-react';

export const AlertsPage: React.FC = () => {
  const { addToast } = useToast();
  const [alerts, setAlerts] = useState<MarineAlert[]>([]);
  const [summary, setSummary] = useState<AlertSummaryMetrics | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const [alList, sum] = await Promise.all([
        alertsService.getAlerts(),
        alertsService.getAlertSummary()
      ]);
      setAlerts(alList);
      setSummary(sum);
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleAcknowledge = async (id: string) => {
    try {
      await alertsService.acknowledgeAlert(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, isAcknowledged: true } : a))
      );
      addToast('success', 'Alert Acknowledged', 'Logged in CMLRE incident monitoring system.');
    } catch (err: any) {
      addToast('error', 'Acknowledge Failed', err.message);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter === 'all') return true;
    return a.severity === severityFilter;
  });

  if (isLoading || !summary) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-ocean-coral" />
            Marine Hazards & Ecological Early Warning Feed
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time environmental anomalies, hypoxia upwelling threats, marine heatwaves, and fisheries stress.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="coral" size="md" dot>
            {summary.unacknowledgedCount} Unacknowledged
          </Badge>
          <Badge variant="cyan" size="md">
            {summary.totalAlerts} Total Incidents
          </Badge>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 space-y-1 border-ocean-coral/30">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Critical Hazards</span>
            <AlertOctagon className="w-4 h-4 text-ocean-coral" />
          </div>
          <p className="text-xl font-bold font-mono text-ocean-coral">{summary.criticalCount}</p>
          <p className="text-[10px] text-slate-400">Severe OMZ Hypoxia</p>
        </Card>

        <Card className="p-4 space-y-1 border-ocean-amber/30">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Warnings</span>
            <AlertTriangle className="w-4 h-4 text-ocean-amber" />
          </div>
          <p className="text-xl font-bold font-mono text-ocean-amber">{summary.warningCount}</p>
          <p className="text-[10px] text-slate-400">Marine Heatwave Spike</p>
        </Card>

        <Card className="p-4 space-y-1 border-ocean-cyan/30">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Advisories</span>
            <ShieldAlert className="w-4 h-4 text-ocean-cyan" />
          </div>
          <p className="text-xl font-bold font-mono text-ocean-cyan">{summary.advisoryCount}</p>
          <p className="text-[10px] text-slate-400">Effort Saturation</p>
        </Card>

        <Card className="p-4 space-y-1 border-marine-800">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Resolved / Ack</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-xl font-bold font-mono text-emerald-400">
            {summary.totalAlerts - summary.unacknowledgedCount}
          </p>
          <p className="text-[10px] text-slate-400">Processed by Team</p>
        </Card>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between gap-4 p-3 rounded-xl bg-marine-900/60 border border-marine-800">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Filter className="w-4 h-4 text-ocean-cyan" />
          <span>Filter by Hazard Severity:</span>
        </div>

        <div className="flex items-center gap-1.5">
          {['all', 'critical', 'warning', 'advisory'].map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                severityFilter === s
                  ? 'bg-ocean-cyan text-marine-950 shadow-sm'
                  : 'bg-marine-950 text-slate-400 hover:text-white border border-marine-800'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onAcknowledge={handleAcknowledge}
          />
        ))}
      </div>
    </div>
  );
};
