import React, { useEffect, useState } from 'react';
import { speciesService } from '../../services/species';
import { SpeciesRecord, SpeciesOccurrence } from '../../types/species';
import { Card, CardHeader } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { 
  Compass, 
  Search, 
  Dna, 
  MapPin, 
  Layers, 
  Info, 
  Thermometer, 
  Waves,
  Eye
} from 'lucide-react';

export const SpeciesExplorerPage: React.FC = () => {
  const [speciesList, setSpeciesList] = useState<SpeciesRecord[]>([]);
  const [search, setSearch] = useState('');
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesRecord | null>(null);
  const [occurrences, setOccurrences] = useState<SpeciesOccurrence[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSpecies = async () => {
    setIsLoading(true);
    try {
      const data = await speciesService.getSpeciesList(search || undefined);
      setSpeciesList(data);
    } catch (err) {
      console.error('Failed to load species', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSpecies();
  }, [search]);

  const handleInspectSpecies = async (sp: SpeciesRecord) => {
    setSelectedSpecies(sp);
    setIsModalOpen(true);
    try {
      const occ = await speciesService.getSpeciesOccurrences(sp.id);
      setOccurrences(occ);
    } catch (err) {
      console.error('Failed to load occurrences', err);
    }
  };

  const getIUCNBadge = (cat: string) => {
    switch (cat) {
      case 'Critically Endangered':
      case 'Endangered':
        return <Badge variant="coral" size="sm">{cat}</Badge>;
      case 'Vulnerable':
      case 'Near Threatened':
        return <Badge variant="amber" size="sm">{cat}</Badge>;
      default:
        return <Badge variant="teal" size="sm">{cat}</Badge>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Compass className="w-5 h-5 text-ocean-teal" />
            Marine Species & Biodiversity Taxonomy
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            WoRMS / OBIS aligned marine species catalogue with occurrence records and linked eDNA evidence.
          </p>
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by scientific name, common name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
          />
        </div>
      </div>

      {/* Species Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CardSkeleton rows={4} />
          <CardSkeleton rows={4} />
        </div>
      ) : speciesList.length === 0 ? (
        <EmptyState
          title="No Marine Species Found"
          description="Try searching with a different scientific or common name."
          actionLabel="Clear Search"
          onAction={() => setSearch('')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {speciesList.map((sp) => (
            <Card
              key={sp.id}
              interactive
              onClick={() => handleInspectSpecies(sp)}
              className="p-5 space-y-4 hover:border-ocean-teal/50 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                {/* Header with Badges */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-white group-hover:text-ocean-cyan transition-colors">
                      {sp.taxonomy.commonName}
                    </h3>
                    <p className="text-xs italic text-slate-300 font-serif font-medium">
                      {sp.taxonomy.scientificName}
                    </p>
                  </div>
                  {getIUCNBadge(sp.iucnRedListCategory)}
                </div>

                {/* Taxonomy Hierarchy Pill */}
                <div className="p-2 rounded-lg bg-marine-950/80 border border-marine-850 text-[11px] font-mono text-slate-300 flex flex-wrap gap-x-3 gap-y-1">
                  <span><b className="text-slate-500 font-sans">Class: </b>{sp.taxonomy.class}</span>
                  <span><b className="text-slate-500 font-sans">Order: </b>{sp.taxonomy.order}</span>
                  <span><b className="text-slate-500 font-sans">Family: </b>{sp.taxonomy.family}</span>
                  {sp.taxonomy.aphiaId && (
                    <span className="text-ocean-cyan"><b className="text-slate-500 font-sans">WoRMS ID: </b>{sp.taxonomy.aphiaId}</span>
                  )}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                  {sp.description}
                </p>
              </div>

              {/* Environmental Envelopes & Occurrence Counts */}
              <div className="space-y-3 pt-3 border-t border-marine-800/80">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Depth Window:</span>
                    <span className="text-white font-bold">
                      {Array.isArray(sp.knownDepthRange) && sp.knownDepthRange.length >= 2 ? `${sp.knownDepthRange[0]}-${sp.knownDepthRange[1]}m` : '—'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Temp Window:</span>
                    <span className="text-ocean-cyan font-bold">
                      {Array.isArray(sp.preferredTemperatureRange) && sp.preferredTemperatureRange.length >= 2 ? `${sp.preferredTemperatureRange[0]}-${sp.preferredTemperatureRange[1]}°C` : '—'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">Occurrences:</span>
                    <span className="text-ocean-teal font-bold">{sp.occurrenceCount.toLocaleString()}</span>
                  </div>
                  <div className="p-2 rounded bg-marine-900 border border-marine-850">
                    <span className="text-[9px] text-slate-400 block font-sans">eDNA Evidence:</span>
                    <span className="text-purple-400 font-bold">{sp.ednaDetectionCount} matches</span>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleInspectSpecies(sp);
                    }}
                  >
                    View Occurrence Records & Lineage
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Species Detail Modal */}
      {selectedSpecies && (
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title={`${selectedSpecies.taxonomy.commonName} (${selectedSpecies.taxonomy.scientificName})`}
          maxWidth="2xl"
        >
          <div className="space-y-5">
            {/* Top Taxonomy Grid */}
            <div className="p-4 rounded-xl bg-marine-950 border border-marine-800 space-y-2">
              <h4 className="text-xs font-semibold text-ocean-cyan uppercase tracking-wider">
                Full WoRMS Taxonomic Hierarchy
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono text-slate-200">
                <div><span className="text-slate-400">Kingdom: </span>{selectedSpecies.taxonomy.kingdom}</div>
                <div><span className="text-slate-400">Phylum: </span>{selectedSpecies.taxonomy.phylum}</div>
                <div><span className="text-slate-400">Class: </span>{selectedSpecies.taxonomy.class}</div>
                <div><span className="text-slate-400">Order: </span>{selectedSpecies.taxonomy.order}</div>
                <div><span className="text-slate-400">Family: </span>{selectedSpecies.taxonomy.family}</div>
                <div><span className="text-slate-400">Genus: </span>{selectedSpecies.taxonomy.genus}</div>
              </div>
            </div>

            {/* Occurrence Records Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                <span>Associated Survey Occurrences & Specimen Events</span>
                <span className="font-mono text-ocean-teal">{occurrences.length} Sample Events</span>
              </h4>

              <div className="glass-panel rounded-xl overflow-hidden border border-marine-800">
                <table className="w-full text-left text-xs font-mono border-collapse">
                  <thead>
                    <tr className="bg-marine-900 border-b border-marine-800 text-[11px] font-semibold text-slate-300">
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Coordinates</th>
                      <th className="py-2.5 px-3">Depth</th>
                      <th className="py-2.5 px-3">Specimens</th>
                      <th className="py-2.5 px-3">Basis of Record</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-marine-850 text-slate-200">
                    {occurrences.map((occ) => (
                      <tr key={occ.id} className="hover:bg-marine-900/50">
                        <td className="py-2 px-3">{occ.eventDate}</td>
                        <td className="py-2 px-3 text-ocean-cyan">{occ.latitude}°N, {occ.longitude}°E</td>
                        <td className="py-2 px-3">{occ.depthMeters}m</td>
                        <td className="py-2 px-3">{occ.individualCount}</td>
                        <td className="py-2 px-3 font-sans">
                          <span className="px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-[10px]">
                            {occ.basisOfRecord}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
