import React, { useEffect, useState } from 'react';
import { fisheriesService } from '../../services/fisheries';
import { FisheriesSummaryMetrics, FisheriesTrendPoint } from '../../types/fisheries';
import { DistributionBarChart } from '../../components/charts/DistributionBarChart';
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart';
import { Card, CardHeader } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Fish, Anchor, Activity, TrendingUp, Ship, MapPin, AlertTriangle } from 'lucide-react';

export const FisheriesExplorerPage: React.FC = () => {
  const [summary, setSummary] = useState<FisheriesSummaryMetrics | null>(null);
  const [trends, setTrends] = useState<FisheriesTrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFisheries = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sum, tr] = await Promise.all([
        fisheriesService.getSummary(),
        fisheriesService.getTrends()
      ]);
      setSummary(sum);
      setTrends(tr);
    } catch (err: any) {
      console.error('Failed to load fisheries data', err);
      setError(err?.message || 'Failed to load fisheries data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFisheries();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="glass-panel rounded-xl p-8 text-center space-y-4 border border-rose-500/30">
        <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-white">Fisheries Data Unavailable</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">{error}</p>
        </div>
        <Button onClick={loadFisheries} variant="secondary" size="sm">
          Retry Loading
        </Button>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  const barSeries = [
    { key: 'pelagicCatchTons', name: 'Pelagic Teleosts (Tons)', color: '#00f0ff' },
    { key: 'demersalCatchTons', name: 'Demersal Finfish (Tons)', color: '#06d6a0' },
    { key: 'crustaceanCatchTons', name: 'Crustaceans & Shrimp (Tons)', color: '#ffb703' }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Fish className="w-5 h-5 text-ocean-amber" />
            Commercial Marine Fisheries & Catch Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Harbor landings, Catch Per Unit Effort (CPUE), mechanized trawler monitoring, and seasonal stock dynamics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="amber" size="md">
            Sustainability Index: {summary.sustainabilityIndex !== null && summary.sustainabilityIndex !== undefined ? `${summary.sustainabilityIndex}/100` : '—'}
          </Badge>
          <Badge variant="cyan" size="md">
            {summary.activeVesselsTracked !== null ? summary.activeVesselsTracked.toLocaleString() : '—'} Vessels Monitored
          </Badge>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Annual Marine Landings</span>
            <Anchor className="w-4 h-4 text-ocean-cyan" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.totalCatchAnnualTons !== null ? summary.totalCatchAnnualTons.toLocaleString() : '—'} <span className="text-xs">Tons</span>
          </p>
          <p className="text-[10px] text-slate-400">All Indian Coastal States</p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Fleet CPUE</span>
            <TrendingUp className="w-4 h-4 text-ocean-teal" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.overallAvgCPUE !== null && summary.overallAvgCPUE !== undefined ? <>{summary.overallAvgCPUE} <span className="text-xs">kg/hour</span></> : '—'}
          </p>
          <p className="text-[10px] text-slate-400">Catch Per Unit Effort</p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Dominant Commercial Stock</span>
            <Fish className="w-4 h-4 text-ocean-amber" />
          </div>
          <p className="text-sm font-bold text-white truncate">{summary.dominantCatchGroup ?? '—'}</p>
          <p className="text-[10px] text-slate-400">62% of Coastal Landings</p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mechanized Vessels</span>
            <Ship className="w-4 h-4 text-ocean-coral" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.activeVesselsTracked !== null ? summary.activeVesselsTracked.toLocaleString() : '—'}
          </p>
          <p className="text-[10px] text-slate-400">Trawlers, Purse Seiners, Liners</p>
        </Card>
      </div>

      {/* Main Charts & Harbor Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Landings Distribution by Quarter */}
        <Card className="lg:col-span-2 p-5 space-y-4">
          <CardHeader
            title="Quarterly Catch Landings Composition (2024 - 2025)"
            subtitle="Breakdown of pelagic, demersal, and crustacean harvest volumes"
          />
          <DistributionBarChart
            data={trends}
            series={barSeries}
            xAxisKey="period"
            height={300}
          />
        </Card>

        {/* Right 1 Col: Top Landing Harbors */}
        <Card className="p-5 space-y-4">
          <CardHeader
            title="Top Fisheries Harbors"
            subtitle="Annual landing volumes across major ports"
          />
          <div className="space-y-2.5">
            {summary.topLandingHarbors.map((h, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-xl bg-marine-900/80 border border-marine-800 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-marine-950 border border-marine-700 flex items-center justify-center font-mono text-[10px] text-ocean-amber">
                    {idx + 1}
                  </span>
                  <span className="font-medium text-white truncate max-w-[140px]">{h.name}</span>
                </div>
                <span className="font-mono text-ocean-cyan font-bold">
                  {h.landingsTons.toLocaleString()} T
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
