import React from 'react';
import { AnalysisParameterConfig, AnalysisType } from '../../types/analysis';
import { Sliders, Play, RotateCcw } from 'lucide-react';
import { Button } from '../ui/Button';

export interface ParameterFormProps {
  parameters: AnalysisParameterConfig;
  onChange: (params: AnalysisParameterConfig) => void;
  onRunAnalysis: () => void;
  isRunning: boolean;
}

export const ParameterForm: React.FC<ParameterFormProps> = ({
  parameters,
  onChange,
  onRunAnalysis,
  isRunning
}) => {
  const independentVars = [
    { id: 'sea_surface_temperature', label: 'Sea Surface Temperature (SST, °C)' },
    { id: 'dissolved_oxygen', label: 'Dissolved Oxygen (DO, mg/L)' },
    { id: 'salinity', label: 'Salinity (PSU)' },
    { id: 'chlorophyll_a', label: 'Chlorophyll-a (mg/m³)' },
    { id: 'depth_meters', label: 'Bathymetric Depth (m)' }
  ];

  const dependentVars = [
    { id: 'species_richness', label: 'Marine Species Richness (Taxa Count)' },
    { id: 'cpue_kg_per_hour', label: 'Fisheries CPUE (kg/hour)' },
    { id: 'shannon_wiener_index', label: 'Shannon-Wiener Biodiversity Index (H\')' },
    { id: 'catch_weight_kg', label: 'Total Catch Weight (kg)' },
    { id: 'edna_detection_abundance', label: 'eDNA Relative Sequence Abundance (%)' }
  ];

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-marine-800 pb-3">
        <Sliders className="w-4 h-4 text-ocean-cyan" />
        <h4 className="text-sm font-semibold text-white">Analysis Configuration & Variables</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Independent Variable (X) */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">
            Independent Variable (X-Axis)
          </label>
          <select
            value={parameters.independentVariable}
            onChange={(e) => onChange({ ...parameters, independentVariable: e.target.value })}
            className="w-full bg-marine-900 border border-marine-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan font-mono"
          >
            {independentVars.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </select>
        </div>

        {/* Dependent Variable (Y) */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">
            Dependent Variable (Y-Axis)
          </label>
          <select
            value={parameters.dependentVariable}
            onChange={(e) => onChange({ ...parameters, dependentVariable: e.target.value })}
            className="w-full bg-marine-900 border border-marine-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan font-mono"
          >
            {dependentVars.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </select>
        </div>

        {/* Region */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">Sampling Sector / Region</label>
          <select
            value={parameters.region || 'Arabian Sea'}
            onChange={(e) => onChange({ ...parameters, region: e.target.value })}
            className="w-full bg-marine-900 border border-marine-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan"
          >
            <option value="Arabian Sea">Arabian Sea Sector (Cochin to Goa Transects)</option>
            <option value="Bay of Bengal">Bay of Bengal Sector (Chennai to Vizag)</option>
            <option value="Lakshadweep">Lakshadweep Archipelago Reefs</option>
            <option value="All Sectors">Combined Indian EEZ Waters</option>
          </select>
        </div>

        {/* Transformation */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">Statistical Normalization</label>
          <select
            value={parameters.transformation || 'none'}
            onChange={(e) => onChange({ ...parameters, transformation: e.target.value as any })}
            className="w-full bg-marine-900 border border-marine-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan"
          >
            <option value="none">Raw Values (Standard OLS)</option>
            <option value="log10">Logarithmic Transformation (log10)</option>
            <option value="normalize_zscore">Z-Score Normalization (Standardized)</option>
          </select>
        </div>
      </div>

      <div className="pt-2 flex justify-end">
        <Button
          onClick={onRunAnalysis}
          isLoading={isRunning}
          variant="primary"
          leftIcon={<Play className="w-4 h-4 fill-current" />}
        >
          Compute Cross-Domain Regression
        </Button>
      </div>
    </div>
  );
};
