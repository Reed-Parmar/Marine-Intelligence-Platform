import React, { useEffect, useState, useRef } from 'react';
import { mlService } from '../../services/ml';
import {
  MLModelInfo,
  AnomalyDetectionResult,
  HabitatSuitabilityResult,
  CatchForecastResult
} from '../../types/ml';
import { DisclaimerBanner } from '../../components/ai/DisclaimerBanner';
import { AnomalyCard } from '../../components/ai/AnomalyCard';
import { HabitatSuitabilityCard } from '../../components/ai/HabitatSuitabilityCard';
import { CatchPredictionCard } from '../../components/ai/CatchPredictionCard';
import { CatchPredictionSimulator } from '../../components/ai/CatchPredictionSimulator';
import { DistributionShiftWorkspace } from '../../components/distributionShift/DistributionShiftWorkspace';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Cpu, Sparkles, Layers, Activity, Fish, TrendingUp } from 'lucide-react';

export const AIInsightsPage: React.FC = () => {
  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyDetectionResult[]>([]);
  const [suitability, setSuitability] = useState<HabitatSuitabilityResult[]>([]);
  const [forecasts, setForecasts] = useState<CatchForecastResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [simSpecies, setSimSpecies] = useState<string>('Indian Oil Sardine (Sardinella longiceps)');

  const simulatorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadAI = async () => {
      setIsLoading(true);
      try {
        const [mods, anoms, suit, fore] = await Promise.all([
          mlService.getModels(),
          mlService.getAnomalies(),
          mlService.getHabitatSuitability(),
          mlService.getCatchForecasts()
        ]);
        setModels(mods);
        setAnomalies(anoms);
        setSuitability(suit);
        setForecasts(fore);
      } catch (err) {
        console.error('Failed to load AI insights', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadAI();
  }, []);

  const handleSimulateClick = (species: string) => {
    setSimSpecies(species);
    if (simulatorRef.current) {
      simulatorRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-ocean-cyan" />
            AI & Machine Learning Decision Support Suite
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Marine anomaly detection, species habitat suitability envelopes, and biomass catch prediction pipelines.
          </p>
        </div>

        <Badge variant="cyan" size="md">
          {models.length} Production Inference Models Active
        </Badge>
      </div>

      {/* Decision Support Advisory Banner */}
      <DisclaimerBanner />

      {/* 1. Active ML Models Overview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-ocean-cyan" />
            Registered Machine Learning Models & Inference Pipelines
          </h3>
          <span className="text-[11px] font-mono text-slate-400">Registry Active</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {models.map((mod) => (
            <Card key={mod.id} className="p-4 space-y-3 border-marine-800 hover:border-ocean-cyan/40 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">{mod.name}</h4>
                  <p className="text-[10px] font-mono text-ocean-cyan">v{mod.version} • {mod.framework}</p>
                </div>
                <Badge variant="teal" size="sm">
                  {(mod.trainingAccuracyF1 * 100).toFixed(1)}% F1
                </Badge>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{mod.description}</p>
              <div className="flex flex-wrap gap-1 pt-1 border-t border-marine-850">
                {mod.inputFeatures.map((f, idx) => (
                  <span key={idx} className="px-1.5 py-0.5 rounded bg-marine-900 border border-marine-800 text-[9px] font-mono text-slate-300">
                    {f}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* 2. Detected Environmental Anomalies */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-ocean-coral" />
            Active Marine Environmental Anomalies & Stress Events
          </h3>
          <Badge variant="coral" size="sm">
            {anomalies.length} Active Alerts
          </Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {anomalies.map((anom) => (
            <AnomalyCard key={anom.id} anomaly={anom} />
          ))}
        </div>
      </div>

      {/* 3. Ecological Habitat Suitability Models */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-ocean-teal" />
            Pelagic Species Habitat Suitability Envelopes (MaxEnt)
          </h3>
          <Badge variant="teal" size="sm">
            MaxEnt Spatial Niche
          </Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {suitability.map((suit, idx) => (
            <HabitatSuitabilityCard key={idx} suitability={suit} />
          ))}
        </div>
      </div>

      {/* 4. Catch Prediction & Commercial Landings (MBLF-Net) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Fish className="w-3.5 h-3.5 text-ocean-cyan" />
              Catch Prediction & Commercial Biomass Yield (MBLF-Net)
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              XGBoost Temporal CNN-LSTM forecaster predicting quarterly marine landings and Catch Per Unit Effort (CPUE).
            </p>
          </div>
          <Badge variant="cyan" size="sm" className="hidden sm:inline-flex">
            MBLF-Net Ensemble
          </Badge>
        </div>

        {/* Live Simulator Tool */}
        <div ref={simulatorRef}>
          <CatchPredictionSimulator key={simSpecies} initialSpecies={simSpecies} />
        </div>

        {/* Forecast Cards Grid */}
        <div className="space-y-2 pt-2">
          <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Quarterly Landings Projections by Stock
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {forecasts.map((fore, idx) => (
              <CatchPredictionCard
                key={idx}
                forecast={fore}
                onSimulate={handleSimulateClick}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 5. Seasonal Species Distribution Shift & Movement Propensity (Step 7 Workspace) */}
      <div className="pt-6 border-t border-marine-800 space-y-4">
        <DistributionShiftWorkspace />
      </div>
    </div>
  );
};

export default AIInsightsPage;
