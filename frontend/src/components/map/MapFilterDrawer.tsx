import React from 'react';
import { Filter, Sliders, Calendar, Compass, RotateCcw } from 'lucide-react';
import { Button } from '../ui/Button';

export interface MapFiltersState {
  region: string;
  depthMax: number;
  species: string;
  variable: string;
}

export interface MapFilterDrawerProps {
  filters: MapFiltersState;
  onChangeFilter: (key: keyof MapFiltersState, val: any) => void;
  onReset: () => void;
}

export const MapFilterDrawer: React.FC<MapFilterDrawerProps> = ({
  filters,
  onChangeFilter,
  onReset
}) => {
  const regions = [
    'All Indian Oceanic Sectors',
    'Arabian Sea',
    'Bay of Bengal',
    'Lakshadweep',
    'Andaman & Nicobar'
  ];

  const oceanVariables = [
    { id: 'all', label: 'All Oceanic Variables' },
    { id: 'sst', label: 'Sea Surface Temp (°C)' },
    { id: 'salinity', label: 'Salinity (PSU)' },
    { id: 'oxygen', label: 'Dissolved Oxygen (mg/L)' },
    { id: 'chlorophyll', label: 'Chlorophyll-a (mg/m³)' }
  ];

  return (
    <div className="glass-panel rounded-2xl p-4 space-y-4 border border-marine-800 bg-marine-950/90 shadow-2xl">
      <div className="flex items-center justify-between border-b border-marine-850 pb-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-white">
          <Filter className="w-4 h-4 text-ocean-cyan" />
          <span>Spatial & Depth Filters</span>
        </div>
        <button
          onClick={onReset}
          className="text-[11px] text-slate-400 hover:text-ocean-cyan flex items-center gap-1 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          Reset
        </button>
      </div>

      {/* Region Selector */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-slate-300">Geographic Region</label>
        <select
          value={filters.region}
          onChange={(e) => onChangeFilter('region', e.target.value)}
          className="w-full bg-marine-900 border border-marine-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-ocean-cyan"
        >
          {regions.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {/* Depth Slice Slider */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-[11px]">
          <span className="font-medium text-slate-300">Max Depth Slice:</span>
          <span className="font-mono text-ocean-cyan font-bold">{filters.depthMax}m</span>
        </div>
        <input
          type="range"
          min="10"
          max="1000"
          step="10"
          value={filters.depthMax}
          onChange={(e) => onChangeFilter('depthMax', Number(e.target.value))}
          className="w-full h-1.5 bg-marine-800 rounded-lg appearance-none cursor-pointer accent-ocean-cyan"
        />
        <div className="flex justify-between text-[9px] text-slate-500 font-mono">
          <span>0m (Surface)</span>
          <span>200m (Mesopelagic)</span>
          <span>1000m+ (Bathy)</span>
        </div>
      </div>

      {/* Variable Focus */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-slate-300">Ocean Parameter Focus</label>
        <select
          value={filters.variable}
          onChange={(e) => onChangeFilter('variable', e.target.value)}
          className="w-full bg-marine-900 border border-marine-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-ocean-cyan"
        >
          {oceanVariables.map((v) => (
            <option key={v.id} value={v.id}>
              {v.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
