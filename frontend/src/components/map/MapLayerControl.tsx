import React from 'react';
import { Waves, Fish, Compass, Dna, AlertTriangle, Layers } from 'lucide-react';

export interface MapLayerState {
  ocean: boolean;
  fisheries: boolean;
  species: boolean;
  edna: boolean;
  anomalies: boolean;
}

export interface MapLayerControlProps {
  layers: MapLayerState;
  onToggleLayer: (layerKey: keyof MapLayerState) => void;
}

export const MapLayerControl: React.FC<MapLayerControlProps> = ({
  layers,
  onToggleLayer
}) => {
  const layerConfigs: {
    key: keyof MapLayerState;
    label: string;
    icon: React.ReactNode;
    color: string;
    activeClass: string;
  }[] = [
    {
      key: 'ocean',
      label: 'Oceanographic CTD',
      icon: <Waves className="w-3.5 h-3.5" />,
      color: '#00f0ff',
      activeClass: 'bg-ocean-cyan/20 border-ocean-cyan text-ocean-cyan shadow-glow-cyan'
    },
    {
      key: 'fisheries',
      label: 'Fisheries Landings',
      icon: <Fish className="w-3.5 h-3.5" />,
      color: '#ffb703',
      activeClass: 'bg-ocean-amber/20 border-ocean-amber text-ocean-amber'
    },
    {
      key: 'species',
      label: 'Species Occurrences',
      icon: <Compass className="w-3.5 h-3.5" />,
      color: '#06d6a0',
      activeClass: 'bg-ocean-teal/20 border-ocean-teal text-ocean-teal'
    },
    {
      key: 'edna',
      label: 'eDNA Detections',
      icon: <Dna className="w-3.5 h-3.5" />,
      color: '#7928ca',
      activeClass: 'bg-purple-500/20 border-purple-400 text-purple-300'
    },
    {
      key: 'anomalies',
      label: 'AI Risk & Anomalies',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      color: '#ff4d6d',
      activeClass: 'bg-ocean-coral/20 border-ocean-coral text-ocean-coral animate-pulse'
    }
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 p-2 rounded-xl bg-marine-950/85 backdrop-blur-md border border-marine-800 shadow-xl">
      <div className="flex items-center gap-1.5 px-2 text-xs font-semibold text-slate-300 border-r border-marine-800 mr-1">
        <Layers className="w-3.5 h-3.5 text-ocean-cyan" />
        <span>Layers:</span>
      </div>

      {layerConfigs.map((cfg) => {
        const isActive = layers[cfg.key];
        return (
          <button
            key={cfg.key}
            onClick={() => onToggleLayer(cfg.key)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isActive
                ? cfg.activeClass
                : 'bg-marine-900/60 border-marine-800 text-slate-400 hover:text-slate-200 hover:bg-marine-800'
            }`}
          >
            {cfg.icon}
            <span>{cfg.label}</span>
          </button>
        );
      })}
    </div>
  );
};
