import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import {
  DistributionShiftPredictionResponse,
  CANONICAL_ARABIAN_SEA_SECTORS,
} from '../../types/distributionShift';
import { Compass } from 'lucide-react';

interface DistributionShiftMapProps {
  prediction: DistributionShiftPredictionResponse | null;
  onSelectSector?: (sector: string) => void;
}

// Custom Marker Icons
const createSourceIcon = () => {
  return L.divIcon({
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background-color: #06d6a0;
        border: 3px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 16px rgba(6, 214, 160, 0.8), 0 0 30px rgba(6, 214, 160, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="width: 6px; height: 6px; background-color: #050b14; border-radius: 50%;"></div>
      </div>
    `,
    className: 'custom-source-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const createTargetIcon = (rank: number, prob: number) => {
  let color = '#00f0ff';
  let glow = 'rgba(0, 240, 255, 0.6)';
  let size = 20;

  if (rank === 1) {
    color = '#00f0ff';
    glow = 'rgba(0, 240, 255, 0.8)';
    size = 24;
  } else if (rank === 2) {
    color = '#38bdf8';
    glow = 'rgba(56, 189, 248, 0.6)';
    size = 20;
  } else if (rank === 3) {
    color = '#fbbf24';
    glow = 'rgba(251, 191, 36, 0.6)';
    size = 18;
  } else {
    color = '#64748b';
    glow = 'rgba(100, 116, 139, 0.3)';
    size = 14;
  }

  return L.divIcon({
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background-color: ${color};
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 12px ${glow};
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: monospace;
        font-size: 10px;
        font-weight: bold;
        color: #050b14;
      ">
        ${rank <= 3 ? rank : ''}
      </div>
    `,
    className: 'custom-target-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

export const DistributionShiftMap: React.FC<DistributionShiftMapProps> = ({
  prediction,
  onSelectSector,
}) => {
  // Center of the Arabian Sea
  const centerLat = 13.5;
  const centerLon = 72.0;

  const srcLat = prediction?.source_coordinates.latitude ?? 10.5;
  const srcLon = prediction?.source_coordinates.longitude ?? 75.5;

  // Build sorted list of all 7 sectors with probabilities
  const sectorList = Object.entries(CANONICAL_ARABIAN_SEA_SECTORS).map(([sector, coords]) => {
    const prob = prediction?.probability_distribution[sector] ?? 0.0;
    return { sector, coords, prob };
  }).sort((a, b) => b.prob - a.prob);

  return (
    <div className="w-full h-full min-h-[480px] rounded-2xl overflow-hidden border border-marine-800 relative z-0 shadow-2xl bg-marine-950">
      {/* Floating Scientific Disclaimer Label */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-2 px-3 py-1.5 rounded-lg bg-marine-950/90 border border-marine-700/80 backdrop-blur-md text-xs font-medium text-slate-200 shadow-lg">
        <span className="w-2 h-2 rounded-full bg-ocean-cyan animate-pulse" />
        <span>Population-level seasonal distribution shift</span>
      </div>

      {/* Floating Mode Context */}
      {prediction && (
        <div className="absolute top-3 right-3 z-[1000] hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-marine-950/90 border border-ocean-cyan/40 backdrop-blur-md text-xs font-mono text-ocean-cyan shadow-lg">
          <span>{prediction.species}</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-300">
            {prediction.forecast.source_season.season_name.split(' ')[0]} → {prediction.forecast.target_season.season_name.split(' ')[0]} (+{prediction.forecast_horizon_months}m)
          </span>
        </div>
      )}

      {/* Floating Map Legend */}
      <div className="absolute bottom-4 right-4 z-[1000] p-3 rounded-xl bg-marine-950/95 border border-marine-700/80 backdrop-blur-md text-xs text-slate-300 space-y-2 shadow-2xl max-w-[240px]">
        <div className="font-semibold text-slate-200 border-b border-marine-800 pb-1 flex items-center gap-1.5">
          <Compass className="w-3.5 h-3.5 text-ocean-cyan" />
          Map Propensity Legend
        </div>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#06d6a0] border border-white shadow-[0_0_8px_#06d6a0]" />
            <span>Current Population Node</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#00f0ff] border border-white shadow-[0_0_8px_#00f0ff]" />
            <span>#1 Top Predicted Shift</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#fbbf24] border border-white shadow-[0_0_8px_#fbbf24]" />
            <span>Secondary Probable Sectors</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-gradient-to-r from-ocean-cyan to-transparent" />
            <span className="text-slate-400">Vector Thickness ∝ Probability</span>
          </div>
        </div>
        <div className="text-[10px] text-slate-400 pt-1 border-t border-marine-800/80">
          Non-telemetry Eulerian propensity vectors.
        </div>
      </div>

      <MapContainer
        center={[centerLat, centerLon]}
        zoom={5}
        scrollWheelZoom={true}
        className="w-full h-full"
        style={{ minHeight: '480px', background: '#050b14' }}
      >
        {/* Dark Ocean Basemap */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a> | CMLRE MoES India'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={18}
        />

        {/* Source Population Node */}
        {prediction && (
          <Marker position={[srcLat, srcLon]} icon={createSourceIcon()}>
            <Popup className="custom-popup">
              <div className="p-2 space-y-1 text-slate-900">
                <p className="font-bold text-xs">Current Observation Origin</p>
                <p className="text-[11px]">{prediction.source_sector}</p>
                <p className="text-[10px] font-mono text-slate-600">
                  {srcLat.toFixed(2)}°N, {srcLon.toFixed(2)}°E
                </p>
                <p className="text-[10px] text-emerald-700 font-semibold">
                  Source: Month {prediction.forecast.source_month} ({prediction.forecast.source_season.season_name})
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Predicted Sector Nodes and Directional Vectors */}
        {sectorList.map(({ sector, coords, prob }, idx) => {
          const rank = idx + 1;
          const [tgtLat, tgtLon] = coords;
          const isSource = prediction && Math.abs(srcLat - tgtLat) < 0.2 && Math.abs(srcLon - tgtLon) < 0.2;

          // Compute polyline styling
          let lineColor = '#00f0ff';
          let weight = Math.max(1.5, prob * 8);
          let opacity = Math.max(0.2, prob * 1.2);
          let dashArray = prob < 0.15 ? '4, 8' : undefined;

          if (rank === 1) {
            lineColor = '#00f0ff';
          } else if (rank === 2) {
            lineColor = '#38bdf8';
          } else if (rank === 3) {
            lineColor = '#fbbf24';
          } else {
            lineColor = '#64748b';
          }

          return (
            <React.Fragment key={sector}>
              {/* Propensity Vector Line (Only draw if prediction exists and target != source) */}
              {prediction && !isSource && (
                <Polyline
                  positions={[
                    [srcLat, srcLon],
                    [tgtLat, tgtLon],
                  ]}
                  pathOptions={{
                    color: lineColor,
                    weight,
                    opacity,
                    dashArray,
                  }}
                >
                  <Tooltip sticky>
                    <span className="font-mono text-xs">
                      {sector}: {(prob * 100).toFixed(1)}% propensity
                    </span>
                  </Tooltip>
                </Polyline>
              )}

              {/* Destination Sector Marker */}
              <Marker
                position={[tgtLat, tgtLon]}
                icon={createTargetIcon(rank, prob)}
                eventHandlers={{
                  click: () => onSelectSector && onSelectSector(sector),
                }}
              >
                <Popup>
                  <div className="p-2 space-y-1.5 text-slate-900 min-w-[180px]">
                    <div className="flex items-center justify-between border-b pb-1">
                      <span className="font-bold text-xs">{sector}</span>
                      <span className="font-mono font-bold text-xs text-cyan-700">
                        {(prob * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600">
                      Rank #{rank} Dispersal Sector
                    </p>
                    <p className="text-[10px] font-mono text-slate-500">
                      Centroid: {tgtLat.toFixed(1)}°N, {tgtLon.toFixed(1)}°E
                    </p>
                    {prediction && (
                      <p className="text-[10px] text-slate-600">
                        Forecast Target: Month {prediction.forecast.target_month} ({prediction.forecast.target_season.season_name})
                      </p>
                    )}
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
};
