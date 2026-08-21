import React, { useEffect, useState } from 'react';
import { oceanService } from '../../services/ocean';
import { OceanSummaryMetrics, OceanTrendPoint, CTDProfilePoint } from '../../types/ocean';
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart';
import { DepthProfileChart } from '../../components/charts/DepthProfileChart';
import { Card, CardHeader } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Waves, Thermometer, Droplets, Wind, Activity, Layers } from 'lucide-react';

export const OceanExplorerPage: React.FC = () => {
  const [summary, setSummary] = useState<OceanSummaryMetrics | null>(null);
  const [trends, setTrends] = useState<OceanTrendPoint[]>([]);
  const [ctdProfile, setCtdProfile] = useState<CTDProfilePoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadOceanData = async () => {
      setIsLoading(true);
      try {
        const [sum, tr, ctd] = await Promise.all([
          oceanService.getSummary(),
          oceanService.getTrends(),
          oceanService.getCTDDepthProfile()
        ]);
        setSummary(sum);
        setTrends(tr);
        setCtdProfile(ctd);
      } catch (err) {
        console.error('Failed to load ocean data', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadOceanData();
  }, []);

  if (isLoading || !summary) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  const series = [
    { key: 'avgSST', name: 'Sea Surface Temp (°C)', color: '#00f0ff' },
    { key: 'avgOxygen', name: 'Dissolved Oxygen (mg/L)', color: '#06d6a0' },
    { key: 'avgChlorophyll', name: 'Chlorophyll-a (mg/m³)', color: '#ffb703' }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Waves className="w-5 h-5 text-ocean-cyan" />
            Physical & Chemical Oceanography Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            CTD hydrographic vertical profiling, thermal stratification, and Oxygen Minimum Zone (OMZ) monitoring.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="cyan" size="md">
            {summary.activeSamplingStations !== null && summary.activeSamplingStations !== undefined ? summary.activeSamplingStations : 8} Active Sampling Transects
          </Badge>
          <Badge variant="teal" size="md">
            {summary.totalCTDCasts !== null ? summary.totalCTDCasts.toLocaleString() : '—'} CTD Casts
          </Badge>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mean SST</span>
            <Thermometer className="w-4 h-4 text-ocean-cyan" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.meanSST !== null && summary.meanSST !== undefined ? `${summary.meanSST}°C` : '—'}
          </p>
          <p className="text-[10px] text-slate-400 font-mono">
            {summary.minSST !== null && summary.maxSST !== null ? `Range: ${summary.minSST}°C - ${summary.maxSST}°C` : 'Indian Ocean Baseline'}
          </p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mean Salinity</span>
            <Droplets className="w-4 h-4 text-ocean-teal" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.meanSalinity !== null && summary.meanSalinity !== undefined ? <>{summary.meanSalinity} <span className="text-xs">PSU</span></> : '—'}
          </p>
          <p className="text-[10px] text-slate-400">Practical Salinity Units</p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mean Dissolved Oxygen</span>
            <Wind className="w-4 h-4 text-ocean-amber" />
          </div>
          <p className="text-xl font-bold font-mono text-white">
            {summary.meanOxygen !== null && summary.meanOxygen !== undefined ? <>{summary.meanOxygen} <span className="text-xs">mg/L</span></> : '—'}
          </p>
          <p className="text-[10px] text-slate-400">Surface Mixed Layer</p>
        </Card>

        <Card className="p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Hypoxic Footprint (OMZ)</span>
            <Activity className="w-4 h-4 text-ocean-coral" />
          </div>
          <p className="text-xl font-bold font-mono text-ocean-coral">
            {summary.hypoxicAreaSqKm !== null && summary.hypoxicAreaSqKm !== undefined ? <>{summary.hypoxicAreaSqKm.toLocaleString()} <span className="text-xs">km²</span></> : 'Active Monitor'}
          </p>
          <p className="text-[10px] text-slate-400 font-mono">&lt; 2.0 mg/L DO Threshold</p>
        </Card>
      </div>

      {/* Main Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Time-Series Seasonal Trends */}
        <Card className="p-5 space-y-4">
          <CardHeader
            title="Multi-Parameter Seasonal Oceanographic Trends"
            subtitle="Monthly average SST, Dissolved Oxygen, and Chlorophyll-a (2025)"
          />
          <TimeSeriesChart data={trends} series={series} height={300} />
        </Card>

        {/* Right: Vertical CTD Depth Cast */}
        <Card className="p-5 space-y-4">
          <CardHeader
            title="Vertical Water Column Profile (0 - 500m Cast)"
            subtitle="Temperature decline, Salinity maximum, and OMZ shoaling depth"
          />
          <DepthProfileChart data={ctdProfile} height={300} />
        </Card>
      </div>
    </div>
  );
};
