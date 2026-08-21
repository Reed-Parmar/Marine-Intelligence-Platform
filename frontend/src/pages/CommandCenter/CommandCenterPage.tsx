import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { marineService } from '../../services/marine';
import { datasetService } from '../../services/datasets';
import { alertsService } from '../../services/alerts';
import { useAuth } from '../../context/AuthContext';
import { MarineSummary } from '../../types/marine';
import { DatasetMetadata } from '../../types/dataset';
import { MarineAlert } from '../../types/alert';
import { 
  Database, 
  Map as MapIcon, 
  Waves, 
  Fish, 
  Dna, 
  Microscope, 
  AlertTriangle, 
  Cpu, 
  ArrowUpRight, 
  Upload, 
  ShieldCheck, 
  Sparkles,
  Layers,
  Compass,
  Users,
  CheckCircle2,
  Server
} from 'lucide-react';
import { Card, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AlertSeverityBadge } from '../../components/alerts/AlertSeverityBadge';
import { QualityScoreBadge } from '../../components/data/QualityScoreBadge';
import { CardSkeleton } from '../../components/ui/Skeleton';

export const CommandCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [summary, setSummary] = useState<MarineSummary | null>(null);
  const [recentDatasets, setRecentDatasets] = useState<DatasetMetadata[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<MarineAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdmin = user?.role === 'admin';

  const loadDashboard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sum, ds, al] = await Promise.all([
        marineService.getSummary(),
        datasetService.getDatasets(),
        alertsService.getAlerts()
      ]);
      setSummary(sum);
      setRecentDatasets(ds.slice(0, 4));
      setRecentAlerts(al.slice(0, 3));
    } catch (err: any) {
      console.error('Failed to load command center summary', err);
      setError(err?.message || 'Failed to load command center summary. Please check backend connection and retry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} rows={2} />
          ))}
        </div>
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
          <h3 className="text-base font-semibold text-white">Dashboard Unavailable</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">{error}</p>
        </div>
        <Button onClick={loadDashboard} variant="secondary" size="sm">
          Retry Loading
        </Button>
      </div>
    );
  }

  const kpis = [
    {
      title: 'Datasets Registered',
      value: summary?.totalDatasets ?? 0,
      sub: 'TXT, CTD, CSV, XLSX',
      icon: Database,
      color: 'text-ocean-cyan',
      link: '/data'
    },
    {
      title: 'Unified Observations',
      value: (summary?.totalObservations ?? 0).toLocaleString(),
      sub: 'Spatial-Temporal Points',
      icon: Layers,
      color: 'text-ocean-teal',
      link: '/map'
    },
    {
      title: 'Catalogued Species',
      value: summary?.totalSpeciesRecorded ?? 0,
      sub: 'WoRMS / Darwin Core',
      icon: Compass,
      color: 'text-emerald-400',
      link: '/species'
    },
    {
      title: 'eDNA Records',
      value: (summary?.totalEdnaDetections ?? 0).toLocaleString(),
      sub: '12S, 16S, COI Barcodes',
      icon: Dna,
      color: 'text-purple-400',
      link: '/edna'
    },
    {
      title: 'Active Scientific Analyses',
      value: 'Completed',
      sub: 'Regression & Trends',
      icon: Microscope,
      color: 'text-ocean-amber',
      link: '/analysis'
    },
    {
      title: 'Ecological Alerts',
      value: summary?.activeAnomalies ?? 0,
      sub: 'Hypoxia & Heatwave',
      icon: AlertTriangle,
      color: 'text-ocean-coral',
      link: '/alerts'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Welcome Banner */}
      <div className="relative rounded-3xl p-6 sm:p-8 overflow-hidden bg-gradient-to-r from-marine-900 via-marine-900 to-marine-950 border border-marine-800 shadow-2xl">
        <div className="absolute right-0 top-0 w-96 h-full bg-radial-at-c from-ocean-cyan/10 to-transparent pointer-events-none" />
        
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-ocean-cyan/10 border border-ocean-cyan/30 text-ocean-cyan text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            <span>CMLRE Scientific Unified Workspace Active</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Indian Marine Data & Living Resources Intelligence
          </h2>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Integrating physical oceanographic casts, commercial fisheries catch metrics, biodiversity records, and high-throughput molecular eDNA evidence for marine conservation and fisheries management.
          </p>

          {/* Role-Specific Quick Action Shortcuts */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {isAdmin ? (
              <>
                <Button
                  onClick={() => navigate('/data')}
                  variant="primary"
                  leftIcon={<ShieldCheck className="w-4 h-4" />}
                >
                  Dataset Governance & Moderation
                </Button>
                <Button
                  onClick={() => navigate('/data/upload')}
                  variant="glow"
                  leftIcon={<Upload className="w-4 h-4" />}
                >
                  Direct Pipeline Ingestion
                </Button>
                <Button
                  onClick={() => navigate('/alerts')}
                  variant="outline"
                  leftIcon={<AlertTriangle className="w-4 h-4 text-ocean-coral" />}
                >
                  System Anomalies & Alerts
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => navigate('/map')}
                  variant="primary"
                  leftIcon={<MapIcon className="w-4 h-4" />}
                >
                  Open 2D Research Map
                </Button>
                <Button
                  onClick={() => navigate('/data/upload')}
                  variant="glow"
                  leftIcon={<Upload className="w-4 h-4" />}
                >
                  Ingest Marine Dataset (TXT/CTD)
                </Button>
                <Button
                  onClick={() => navigate('/analysis')}
                  variant="outline"
                  leftIcon={<Microscope className="w-4 h-4" />}
                >
                  Scientific Correlation Studio
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Top Right Admin / Researcher Badge */}
        <div className="hidden lg:block absolute right-8 bottom-8 p-4 rounded-2xl bg-marine-950/80 border border-marine-800 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isAdmin ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-ocean-cyan/20 text-ocean-cyan border border-ocean-cyan/30'}`}>
              {isAdmin ? <ShieldCheck className="w-5 h-5" /> : <Compass className="w-5 h-5" />}
            </div>
            <div>
              <p className="text-xs font-bold text-white uppercase tracking-wider">{user?.role || 'Researcher'} Console</p>
              <p className="text-[11px] text-slate-400 font-mono">{user?.email || 'authenticated user'}</p>
            </div>
          </div>
        </div>
      </div>


      {/* 6 Key Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <Card
              key={idx}
              interactive
              onClick={() => navigate(kpi.link)}
              className="group p-4 flex flex-col justify-between hover:border-ocean-cyan/50"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-slate-400">{kpi.title}</span>
                <Icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className="mt-3">
                <div className="text-xl font-bold font-mono text-white group-hover:text-ocean-cyan transition-colors">
                  {kpi.value}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">{kpi.sub}</div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Main Grid: Regional Oceanic Breakdown + Active Alerts Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Regional Oceanic Sectors */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Indian Oceanic Sector Coverage</h3>
              <p className="text-xs text-slate-400">PostGIS unified spatial records across key marine zones</p>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate('/map')}
              rightIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
            >
              Spatial View
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {summary?.regionsBreakdown.map((r, idx) => (
              <Card key={idx} className="p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-marine-800 pb-2">
                  <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Waves className="w-3.5 h-3.5 text-ocean-cyan" />
                    {r.region}
                  </h4>
                  <Badge variant="cyan" size="sm">Active</Badge>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Obs:</span>
                    <span className="text-white font-bold">{r.observationCount.toLocaleString()}</span>
                  </div>
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Species:</span>
                    <span className="text-ocean-teal font-bold">{r.speciesCount}</span>
                  </div>
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Vessels:</span>
                    <span className="text-ocean-amber font-bold">{r.activeVessels}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Recent Ingested Datasets Table Preview */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-white">Recent Marine Ingestion Catalogue</h3>
              <Button size="sm" variant="ghost" onClick={() => navigate('/data')}>
                View All Datasets ({summary?.totalDatasets})
              </Button>
            </div>
            <div className="glass-panel rounded-2xl p-2 divide-y divide-marine-850 border border-marine-800">
              {recentDatasets.map((d) => (
                <div
                  key={d.id}
                  onClick={() => navigate(`/data/datasets/${d.id}`)}
                  className="p-3.5 flex items-center justify-between hover:bg-marine-900/60 transition-colors cursor-pointer rounded-xl"
                >
                  <div className="space-y-0.5 max-w-md">
                    <p className="text-xs font-semibold text-white truncate hover:text-ocean-cyan">{d.title}</p>
                    <p className="text-[11px] text-slate-400 truncate">{d.source} • {d.rowCount.toLocaleString()} rows</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <QualityScoreBadge score={d.qualityScore} status={d.qualityStatus} size="sm" />
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300">
                      {d.format}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Active Alerts & Early Warning */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Active Marine Hazards</h3>
              <p className="text-xs text-slate-400">Decision support alerts</p>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate('/alerts')}
              rightIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
            >
              All Alerts
            </Button>
          </div>

          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div
                key={alert.id}
                onClick={() => navigate('/alerts')}
                className="glass-panel rounded-xl p-4 border border-marine-800 space-y-2 hover:border-ocean-coral/50 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-semibold text-white leading-tight">{alert.title}</h4>
                  <AlertSeverityBadge severity={alert.severity} />
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-2">{alert.description}</p>
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-marine-850">
                  <span>{alert.region}</span>
                  <span className="text-ocean-cyan">{alert.confidencePercent}% Conf</span>
                </div>
              </div>
            ))}
          </div>

          {/* Scientific Fusion Callout */}
          <div className="glass-panel rounded-2xl p-5 border border-ocean-cyan/40 bg-gradient-to-b from-marine-900 to-marine-950 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-ocean-cyan">
              <Cpu className="w-4 h-4" />
              <span>Cross-Domain Spatial Fusion</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Explore how changes in ocean temperature and dissolved oxygen directly correlate with fisheries catch per unit effort and eDNA species detections across 45 transect stations.
            </p>
            <Button
              onClick={() => navigate('/analysis')}
              size="sm"
              variant="primary"
              className="w-full"
            >
              Launch Scientific Correlation Engine
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
