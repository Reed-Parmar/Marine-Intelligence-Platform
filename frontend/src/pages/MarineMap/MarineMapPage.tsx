import React, { useEffect, useState } from 'react';
import { marineService } from '../../services/marine';
import { MarineObservation, CrossDomainLocationDetail } from '../../types/marine';
import { MarineMap } from '../../components/map/MarineMap';
import { MapLayerControl, MapLayerState } from '../../components/map/MapLayerControl';
import { MapFilterDrawer, MapFiltersState } from '../../components/map/MapFilterDrawer';
import { LocationInspector } from '../../components/map/LocationInspector';
import { MapLegend } from '../../components/map/MapLegend';
import { DistributionShiftWorkspace } from '../../components/distributionShift/DistributionShiftWorkspace';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { MapPin, Sliders, Layers, Sparkles, Compass } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const MarineMapPage: React.FC = () => {
  const [mapMode, setMapMode] = useState<'observations' | 'distribution_shift'>('observations');
  const [observations, setObservations] = useState<MarineObservation[]>([]);
  const [selectedObs, setSelectedObs] = useState<MarineObservation | null>(null);
  const [locationDetail, setLocationDetail] = useState<CrossDomainLocationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const [activeLayers, setActiveLayers] = useState<MapLayerState>({
    ocean: true,
    fisheries: true,
    species: true,
    edna: true,
    anomalies: true
  });

  const [filters, setFilters] = useState<MapFiltersState>({
    region: 'All Indian Oceanic Sectors',
    depthMax: 500,
    species: '',
    variable: 'all'
  });

  const loadObservations = async () => {
    setIsLoading(true);
    try {
      const data = await marineService.getObservations({
        depthMax: filters.depthMax,
        species: filters.species || undefined
      });
      setObservations(data);
    } catch (err) {
      console.error('Failed to load map observations', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (mapMode === 'observations') {
      loadObservations();
    }
  }, [filters, mapMode]);

  const handleToggleLayer = (key: keyof MapLayerState) => {
    setActiveLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSelectObservation = async (obs: MarineObservation) => {
    setSelectedObs(obs);
    try {
      const detail = await marineService.getLocationDetail(obs.latitude, obs.longitude);
      setLocationDetail(detail);
    } catch (err) {
      console.error('Failed to load location fusion details', err);
    }
  };

  const handleResetFilters = () => {
    setFilters({
      region: 'All Indian Oceanic Sectors',
      depthMax: 500,
      species: '',
      variable: 'all'
    });
  };

  return (
    <div className="space-y-4 animate-fade-in relative min-h-[calc(100vh-6.5rem)] flex flex-col">
      {/* Top Floating Controls & Mode Switcher Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 z-10 bg-marine-950/60 p-2 rounded-xl border border-marine-800/80 backdrop-blur-md">
        {/* Mode Switcher Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-marine-900 border border-marine-800">
          <button
            onClick={() => setMapMode('observations')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              mapMode === 'observations'
                ? 'bg-ocean-cyan text-marine-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Observation & Sensor Casts</span>
          </button>

          <button
            onClick={() => setMapMode('distribution_shift')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              mapMode === 'distribution_shift'
                ? 'bg-ocean-cyan text-marine-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Seasonal Distribution Shift Studio</span>
          </button>
        </div>

        {/* Observation-Specific Controls */}
        {mapMode === 'observations' && (
          <div className="flex items-center gap-2">
            <MapLayerControl
              layers={activeLayers}
              onToggleLayer={handleToggleLayer}
            />

            <Button
              size="sm"
              variant={isFilterOpen ? 'glow' : 'outline'}
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              leftIcon={<Sliders className="w-3.5 h-3.5" />}
            >
              {isFilterOpen ? 'Hide Filters' : 'Depth & Region Filters'}
            </Button>

            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-marine-950/80 border border-marine-800 text-xs font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-ocean-cyan animate-pulse" />
              <span>{observations.length} Sampling Casts Active</span>
            </div>
          </div>
        )}
      </div>

      {/* Mode View Switching */}
      {mapMode === 'distribution_shift' ? (
        <div className="flex-1">
          <DistributionShiftWorkspace />
        </div>
      ) : (
        /* Main Map Container for Observations */
        <div className="flex-1 relative rounded-2xl overflow-hidden border border-marine-800 shadow-2xl min-h-[560px]">
          {isLoading ? (
            <div className="w-full h-full flex items-center justify-center bg-marine-950 min-h-[560px]">
              <CardSkeleton rows={4} />
            </div>
          ) : (
            <MarineMap
              observations={observations}
              activeLayers={activeLayers}
              onSelectObservation={handleSelectObservation}
              selectedObservationId={selectedObs?.id}
            />
          )}

          {/* Floating Filter Drawer Over Map */}
          {isFilterOpen && (
            <div className="absolute top-4 right-4 z-20 w-80 animate-slide-up">
              <MapFilterDrawer
                filters={filters}
                onChangeFilter={(k, v) => setFilters((prev) => ({ ...prev, [k]: v }))}
                onReset={handleResetFilters}
              />
            </div>
          )}

          {/* Floating Location Fusion Inspector Card */}
          {locationDetail && (
            <div className="absolute top-4 left-4 z-20 animate-slide-up">
              <LocationInspector
                location={locationDetail}
                onClose={() => {
                  setLocationDetail(null);
                  setSelectedObs(null);
                }}
              />
            </div>
          )}

          {/* Floating Bottom Right Legend */}
          <div className="absolute bottom-4 right-4 z-10 hidden sm:block">
            <MapLegend />
          </div>
        </div>
      )}
    </div>
  );
};

export default MarineMapPage;
