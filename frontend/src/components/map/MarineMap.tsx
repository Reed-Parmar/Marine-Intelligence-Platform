import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MarineObservation } from '../../types/marine';
import { MapLayerState } from './MapLayerControl';
import { Waves, Fish, Compass, Dna, AlertTriangle } from 'lucide-react';

export interface MarineMapProps {
  observations: MarineObservation[];
  activeLayers: MapLayerState;
  onSelectObservation: (obs: MarineObservation) => void;
  selectedObservationId?: string;
}

// Custom SVG-based Leaflet markers for dark marine theme
const createDomainIcon = (domain: string, isSelected: boolean) => {
  let color = '#00f0ff';
  let glow = 'rgba(0, 240, 255, 0.4)';
  if (domain === 'fisheries') {
    color = '#ffb703';
    glow = 'rgba(255, 183, 3, 0.4)';
  } else if (domain === 'biodiversity') {
    color = '#06d6a0';
    glow = 'rgba(6, 214, 160, 0.4)';
  } else if (domain === 'molecular_edna') {
    color = '#a855f7';
    glow = 'rgba(168, 85, 247, 0.4)';
  } else if (domain === 'cross_domain') {
    color = '#ff4d6d';
    glow = 'rgba(255, 77, 109, 0.5)';
  }

  const size = isSelected ? 22 : 14;
  const border = isSelected ? '3px solid #ffffff' : '2px solid #050b14';

  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${color};
      border: ${border};
      border-radius: 50%;
      box-shadow: 0 0 12px ${glow};
      cursor: pointer;
      transition: transform 0.2s;
    "></div>
  `;

  return L.divIcon({
    html,
    className: 'custom-marine-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

export const MarineMap: React.FC<MarineMapProps> = ({
  observations,
  activeLayers,
  onSelectObservation,
  selectedObservationId
}) => {
  const centerLat = 12.5;
  const centerLon = 76.5;

  const visibleObservations = observations.filter((obs) => {
    if (obs.domain === 'oceanography' && !activeLayers.ocean) return false;
    if (obs.domain === 'fisheries' && !activeLayers.fisheries) return false;
    if (obs.domain === 'biodiversity' && !activeLayers.species) return false;
    if (obs.domain === 'molecular_edna' && !activeLayers.edna) return false;
    if (obs.anomalyFlag && !activeLayers.anomalies) return false;
    return true;
  });

  return (
    <div className="w-full h-full min-h-[520px] rounded-2xl overflow-hidden border border-marine-800 relative z-0 shadow-2xl">
      <MapContainer
        center={[centerLat, centerLon]}
        zoom={6}
        scrollWheelZoom={true}
        className="w-full h-full"
        style={{ minHeight: '520px', background: '#050b14' }}
      >
        {/* Dark Ocean Basemap (CartoDB Dark Matter) */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a> | CMLRE MoES India'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={18}
        />

        {/* Observation Markers */}
        {visibleObservations.map((obs) => {
          const isSelected = selectedObservationId === obs.id;
          const icon = createDomainIcon(obs.domain, isSelected);

          return (
            <Marker
              key={obs.id}
              position={[obs.latitude, obs.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectObservation(obs)
              }}
            >
              <Popup className="custom-marine-popup">
                <div className="p-1 space-y-1.5 min-w-[200px]">
                  <div className="flex items-center justify-between border-b border-marine-800 pb-1 text-xs font-bold text-ocean-cyan">
                    <span>{obs.stationId || 'Station Cast'}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{obs.region}</span>
                  </div>
                  <div className="text-xs space-y-1 text-slate-200">
                    <p className="font-semibold text-white truncate">{obs.speciesName || 'Oceanographic CTD Station'}</p>
                    {obs.temperature && (
                      <div className="flex justify-between text-[11px] font-mono">
                        <span className="text-slate-400">SST:</span>
                        <span className="text-white">{obs.temperature}°C</span>
                      </div>
                    )}
                    {obs.dissolvedOxygen && (
                      <div className="flex justify-between text-[11px] font-mono">
                        <span className="text-slate-400">Dissolved Oxygen:</span>
                        <span className={obs.dissolvedOxygen < 2.0 ? 'text-ocean-coral font-bold' : 'text-emerald-400'}>
                          {obs.dissolvedOxygen} mg/L
                        </span>
                      </div>
                    )}
                    {obs.catchWeightKg && (
                      <div className="flex justify-between text-[11px] font-mono">
                        <span className="text-slate-400">Catch Weight:</span>
                        <span className="text-ocean-amber">{obs.catchWeightKg} kg</span>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => onSelectObservation(obs)}
                    className="w-full mt-2 py-1 px-2 rounded bg-ocean-cyan text-marine-950 text-xs font-bold hover:bg-cyan-300 transition-colors"
                  >
                    Inspect Full Cross-Domain Fusion
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};
