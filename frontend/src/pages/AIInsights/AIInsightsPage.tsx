import React, { useEffect, useState } from 'react';
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
import { PredictionCard } from '../../components/ai/PredictionCard';
import { Card, CardHeader } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Cpu, Sparkles, Layers, Activity, ShieldCheck } from 'lucide-react';

export const AIInsightsPage: React.FC = () => {
  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyDetectionResult[]>([]);
  const [suitability, setSuitability] = useState<HabitatSuitabilityResult[]>([]);
  const [forecasts, setForecasts] = useState<CatchForecastResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-ocean-cyan" />
            AI & Machine Learning Decision Support Suite
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Marine anomaly detection, species habitat suitability envelopes, and biomass yield projections.
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
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Registered Machine Learning Models & Inference Pipelines
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {models.map((mod) => (
            <Card key={mod.id} className="p-4 space-y-3 border-marine-800">
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
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Active Marine Environmental Anomalies & Stress Events
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {anomalies.map((anom) => (
            <AnomalyCard key={anom.id} anomaly={anom} />
          ))}
        </div>
      </div>

      {/* 3. Ecological Habitat Suitability Models */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Pelagic Species Habitat Suitability Envelopes (MaxEnt)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {suitability.map((suit, idx) => (
            <HabitatSuitabilityCard key={idx} suitability={suit} />
          ))}
        </div>
      </div>

      {/* 4. Catch Landings & Biomass Forecasting */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Quarterly Commercial Catch Forecasts (LSTM Ensemble)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {forecasts.map((fore, idx) => (
            <PredictionCard key={idx} forecast={fore} />
          ))}
        </div>
      </div>
    </div>
  );
};
