import React from 'react';
import {
  DistributionShiftPredictionResponse,
} from '../../types/distributionShift';
import {
  X,
  ShieldCheck,
  Compass,
  Calendar,
  Layers,
  Thermometer,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  prediction: DistributionShiftPredictionResponse | null;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  prediction,
}) => {
  if (!isOpen || !prediction) return null;

  const {
    species,
    source_sector,
    source_coordinates,
    forecast_horizon_months,
    forecast,
    top_prediction,
    top_3_predictions,
    confidence_level,
    confidence_tier,
    environmental_context_available,
    environmental_inputs,
    markov_baseline_comparison,
    model_metadata,
    limitations,
  } = prediction;

  const getConfidenceBadgeVariant = (level: string): 'teal' | 'amber' | 'coral' => {
    switch (level) {
      case 'HIGH':
        return 'teal';
      case 'MODERATE':
        return 'amber';
      case 'LOW':
      default:
        return 'coral';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-marine-950/80 backdrop-blur-sm animate-fade-in flex justify-end">
      {/* Backdrop click to close */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Drawer Container */}
      <div className="relative w-full max-w-2xl h-full bg-marine-900 border-l border-marine-700/80 shadow-2xl overflow-y-auto flex flex-col z-10 animate-slide-left">
        {/* Header */}
        <div className="sticky top-0 bg-marine-900/95 backdrop-blur-md p-5 border-b border-marine-800 flex items-center justify-between z-20">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-ocean-cyan animate-pulse" />
              <h3 className="text-base font-bold text-white tracking-wide">
                Scientific Evidence & Model Trace
              </h3>
            </div>
            <p className="text-xs font-mono text-ocean-cyan">
              {species} • {forecast_horizon_months}-Month Forecast Horizon
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-marine-800 text-slate-300 hover:text-white hover:bg-marine-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 text-sm text-slate-200">
          {/* Confidence & Prediction Banner */}
          <div className="p-4 rounded-xl bg-marine-950/80 border border-marine-700/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                Primary Predicted Sector
              </span>
              <Badge variant={getConfidenceBadgeVariant(confidence_level)} size="sm">
                {confidence_level} CONFIDENCE
              </Badge>
            </div>
            <div className="flex items-baseline justify-between">
              <h4 className="text-lg font-bold text-ocean-cyan">
                {top_prediction.sector}
              </h4>
              <span className="text-xl font-mono font-bold text-white">
                {(top_prediction.probability * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-xs text-slate-300 border-t border-marine-800 pt-2 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-ocean-cyan shrink-0" />
              {confidence_tier}
            </p>
          </div>

          {/* Temporal & Spatial Transition Context */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Temporal */}
            <div className="p-4 rounded-xl bg-marine-950/50 border border-marine-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                <Calendar className="w-3.5 h-3.5 text-ocean-cyan" />
                Monsoon Temporal Regime
              </div>
              <div className="text-xs space-y-1.5 pt-1">
                <div>
                  <span className="text-slate-400">Source: </span>
                  <span className="font-semibold text-white">
                    Month {forecast.source_month} ({forecast.source_season.season_name})
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Target (+{forecast_horizon_months}m): </span>
                  <span className="font-semibold text-emerald-400">
                    Month {forecast.target_month} ({forecast.target_season.season_name})
                  </span>
                </div>
              </div>
            </div>

            {/* Spatial */}
            <div className="p-4 rounded-xl bg-marine-950/50 border border-marine-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                <Compass className="w-3.5 h-3.5 text-ocean-cyan" />
                Spatial Coordinates
              </div>
              <div className="text-xs space-y-1.5 pt-1">
                <div>
                  <span className="text-slate-400">Source Sector: </span>
                  <span className="font-semibold text-white">{source_sector}</span>
                </div>
                <div>
                  <span className="text-slate-400">Coordinates: </span>
                  <span className="font-mono text-slate-200">
                    {source_coordinates.latitude.toFixed(2)}°N, {source_coordinates.longitude.toFixed(2)}°E
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Model Architecture & Baseline Comparison */}
          <div className="p-4 rounded-xl bg-marine-950/50 border border-marine-800 space-y-3">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-ocean-cyan" />
              Markov Prior vs Full XGBoost Posterior
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800">
                <span className="text-slate-400 block mb-1">Empirical Markov Baseline</span>
                <span className="font-semibold text-slate-200 block">
                  {markov_baseline_comparison.top_markov_sector}
                </span>
                <span className="text-sm font-mono text-cyan-400 font-bold">
                  {(markov_baseline_comparison.markov_probability * 100).toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 block mt-1">
                  {markov_baseline_comparison.fallback_description}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-marine-900/80 border border-ocean-cyan/30">
                <span className="text-ocean-cyan block mb-1 font-semibold">Full XGBoost (With CTD & Spatial)</span>
                <span className="font-semibold text-white block">
                  {top_prediction.sector}
                </span>
                <span className="text-sm font-mono text-emerald-400 font-bold">
                  {(top_prediction.probability * 100).toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-400 block mt-1">
                  Validated Out-of-Fold Ensemble
                </span>
              </div>
            </div>
          </div>

          {/* Environmental Sensor Profile */}
          <div className="p-4 rounded-xl bg-marine-950/50 border border-marine-800 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Thermometer className="w-3.5 h-3.5 text-ocean-cyan" />
                In-Situ Physicochemical Profile
              </h4>
              <Badge variant={environmental_context_available ? 'cyan' : 'slate'} size="sm">
                {environmental_context_available ? 'Sensor Context Available' : 'No Sensor Context (NaN Route)'}
              </Badge>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-marine-900/60 border border-marine-800">
                <span className="text-slate-400 block text-[11px]">SST</span>
                <span className="text-white font-semibold">
                  {environmental_inputs.sst_celsius != null ? `${environmental_inputs.sst_celsius} °C` : 'Unobserved'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-marine-900/60 border border-marine-800">
                <span className="text-slate-400 block text-[11px]">Salinity</span>
                <span className="text-white font-semibold">
                  {environmental_inputs.salinity_psu != null ? `${environmental_inputs.salinity_psu} PSU` : 'Unobserved'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-marine-900/60 border border-marine-800">
                <span className="text-slate-400 block text-[11px]">Dissolved O₂</span>
                <span className="text-white font-semibold">
                  {environmental_inputs.dissolved_oxygen_mgl != null ? `${environmental_inputs.dissolved_oxygen_mgl} mg/L` : 'Unobserved'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-marine-900/60 border border-marine-800">
                <span className="text-slate-400 block text-[11px]">Chlorophyll-a</span>
                <span className="text-white font-semibold">
                  {environmental_inputs.chlorophyll_mg_m3 != null ? `${environmental_inputs.chlorophyll_mg_m3} mg/m³` : 'Unobserved'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-marine-900/60 border border-marine-800">
                <span className="text-slate-400 block text-[11px]">Seafloor Depth</span>
                <span className="text-white font-semibold">
                  {environmental_inputs.mean_depth_meters != null ? `${environmental_inputs.mean_depth_meters} m` : 'Unobserved'}
                </span>
              </div>
            </div>
          </div>

          {/* Model Provenance & Empirical Validation */}
          <div className="p-4 rounded-xl bg-marine-950/50 border border-marine-800 space-y-3">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-ocean-cyan" />
              Model Provenance & Rigorous Validation
            </h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between border-b border-marine-800/60 pb-1.5">
                <span className="text-slate-400">Model Version:</span>
                <span className="font-mono text-slate-200">{model_metadata.model_version}</span>
              </div>
              <div className="flex justify-between border-b border-marine-800/60 pb-1.5">
                <span className="text-slate-400">Training Provenance:</span>
                <span className="text-slate-200">{model_metadata.training_period}</span>
              </div>
              <div className="flex justify-between border-b border-marine-800/60 pb-1.5">
                <span className="text-slate-400">Shifted-Only Top-1 Accuracy:</span>
                <span className="font-mono font-semibold text-emerald-400">48.97% (+6.8% vs Markov)</span>
              </div>
              <div className="flex justify-between border-b border-marine-800/60 pb-1.5">
                <span className="text-slate-400">Shifted-Only Top-3 Accuracy:</span>
                <span className="font-mono font-semibold text-emerald-400">98.29%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Overall Historical Top-1 Accuracy:</span>
                <span className="font-mono font-semibold text-slate-200">74.78%</span>
              </div>
            </div>
          </div>

          {/* Scientific Limitations & Non-Telemetry Advisory */}
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-2">
            <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              Scientific Scope & Limitations
            </h4>
            <ul className="text-xs text-rose-200/90 space-y-1.5 list-disc pl-4">
              {limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-auto p-4 border-t border-marine-800 bg-marine-950 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close Evidence Trace
          </Button>
        </div>
      </div>
    </div>
  );
};
