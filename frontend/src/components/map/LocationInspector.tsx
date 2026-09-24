import React from 'react';
import { CrossDomainLocationDetail } from '../../types/marine';
import { 
  X, 
  MapPin, 
  Waves, 
  Fish, 
  Compass, 
  Dna, 
  Cpu, 
  AlertTriangle,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { Badge } from '../ui/Badge';

export interface LocationInspectorProps {
  location: CrossDomainLocationDetail | null;
  onClose: () => void;
}

export const LocationInspector: React.FC<LocationInspectorProps> = ({ location, onClose }) => {
  if (!location) return null;

  return (
    <div className="glass-panel rounded-2xl p-5 border border-ocean-cyan/50 bg-marine-950/95 shadow-2xl space-y-5 animate-slide-up max-w-md w-full max-h-[85vh] overflow-y-auto custom-scrollbar">
      {/* Header with Coordinates */}
      <div className="flex items-start justify-between border-b border-marine-800 pb-3">
        <div>
          <div className="flex items-center gap-1.5 text-xs text-ocean-cyan font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Unified Spatial-Temporal Fusion</span>
          </div>
          <h3 className="text-sm font-bold text-white mt-1">{location.region}</h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Lat: {location.coordinates.latitude}°N | Lon: {location.coordinates.longitude}°E | Depth: {location.bathymetryDepth}m
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-marine-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 1. Oceanography Domain Slice */}
      <div className="p-3 rounded-xl bg-marine-900/80 border border-ocean-cyan/30 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-ocean-cyan">
          <div className="flex items-center gap-1.5">
            <Waves className="w-3.5 h-3.5" />
            <span>Physical & Chemical Oceanography</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
          <div className="p-2 rounded bg-marine-950 border border-marine-850">
            <span className="text-[10px] text-slate-400 block font-sans">Sea Surface Temp:</span>
            <span className="text-white font-bold">{location.oceanography.seaSurfaceTemperature}°C</span>
          </div>
          <div className="p-2 rounded bg-marine-950 border border-marine-850">
            <span className="text-[10px] text-slate-400 block font-sans">Salinity:</span>
            <span className="text-white font-bold">{location.oceanography.salinity} PSU</span>
          </div>
          <div className="p-2 rounded bg-marine-950 border border-marine-850">
            <span className="text-[10px] text-slate-400 block font-sans">Dissolved Oxygen:</span>
            <span className={`font-bold ${location.oceanography.dissolvedOxygen < 2.0 ? 'text-ocean-coral' : 'text-emerald-400'}`}>
              {location.oceanography.dissolvedOxygen} mg/L
            </span>
          </div>
          <div className="p-2 rounded bg-marine-950 border border-marine-850">
            <span className="text-[10px] text-slate-400 block font-sans">Chlorophyll-a:</span>
            <span className="text-white font-bold">{location.oceanography.chlorophyllA} mg/m³</span>
          </div>
        </div>
      </div>

      {/* 2. Fisheries Domain Slice */}
      <div className="p-3 rounded-xl bg-marine-900/80 border border-ocean-amber/30 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-ocean-amber">
          <div className="flex items-center gap-1.5">
            <Fish className="w-3.5 h-3.5" />
            <span>Commercial Fisheries & CPUE</span>
          </div>
          <Badge variant="amber" size="sm">{location.fisheries.fishingPressureLevel} Pressure</Badge>
        </div>
        <p className="text-xs text-slate-300 font-medium">
          <span className="text-slate-400">Dominant Catch: </span>{location.fisheries.dominantCatch}
        </p>
        <div className="flex justify-between text-xs font-mono text-slate-300">
          <span>CPUE: <b className="text-white">{location.fisheries.cpueKgPerHour} kg/hr</b></span>
          <span>Gear: <b className="text-white">{location.fisheries.dominantGear}</b></span>
        </div>
      </div>

      {/* 3. Biodiversity & Species Occurrence */}
      <div className="p-3 rounded-xl bg-marine-900/80 border border-ocean-teal/30 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-ocean-teal">
          <div className="flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5" />
            <span>Biodiversity & Taxa Recorded</span>
          </div>
          <span className="text-[11px] font-mono font-bold text-white">
            {location.biodiversity.speciesRecordedCount} Species
          </span>
        </div>
        <div className="flex flex-wrap gap-1">
          {location.biodiversity.keySpeciesPresent.map((sp, idx) => (
            <span key={idx} className="px-2 py-0.5 rounded bg-marine-950 border border-marine-800 text-[10px] italic text-slate-300">
              {sp}
            </span>
          ))}
        </div>
      </div>

      {/* 4. Molecular eDNA Matches */}
      <div className="p-3 rounded-xl bg-marine-900/80 border border-purple-500/30 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-purple-300">
          <div className="flex items-center gap-1.5">
            <Dna className="w-3.5 h-3.5" />
            <span>Molecular eDNA Detections</span>
          </div>
          <span className="text-[11px] font-mono text-purple-400">{location.molecularEdna.taxaIdentified} Taxa Identified</span>
        </div>
        <div className="space-y-1.5">
          {location.molecularEdna.topDetections.map((det, idx) => (
            <div key={idx} className="flex items-center justify-between text-[11px] p-1.5 rounded bg-marine-950 border border-marine-850">
              <span className="italic text-slate-200">{det.species}</span>
              <span className="font-mono text-ocean-teal font-bold">{(det.confidence * 100).toFixed(0)}% ({det.marker})</span>
            </div>
          ))}
        </div>
      </div>

      {/* 5. AI Prediction & Decision Support */}
      <div className="p-3 rounded-xl bg-gradient-to-r from-marine-900 to-marine-950 border border-ocean-cyan/40 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-ocean-cyan">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" />
            <span>AI Decision Support Insight</span>
          </div>
          <Badge variant="cyan" size="sm">{location.aiPrediction.habitatSuitabilityPercent}% Suitability</Badge>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{location.aiPrediction.recommendation}</p>
        <p className="text-[10px] text-slate-400 italic pt-1 border-t border-marine-850">
          * AI decision-support aid based on CMLRE multi-variable regression. Not intended as sole operational directive.
        </p>
      </div>
    </div>
  );
};
