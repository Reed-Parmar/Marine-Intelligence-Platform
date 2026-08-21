import React from 'react';

export const MapLegend: React.FC = () => {
  const items = [
    { label: 'Oceanographic Station (CTD)', color: '#00f0ff' },
    { label: 'Fisheries Landings / Effort', color: '#ffb703' },
    { label: 'Species Occurrence Record', color: '#06d6a0' },
    { label: 'eDNA Sampling Point', color: '#a855f7' },
    { label: 'Hypoxia / Heatwave Anomaly', color: '#ff4d6d' }
  ];

  return (
    <div className="glass-panel rounded-xl p-3 bg-marine-950/90 border border-marine-800 text-[11px] space-y-2 shadow-lg">
      <p className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Map Symbology</p>
      <div className="space-y-1.5">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0 shadow-sm"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-slate-300">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
