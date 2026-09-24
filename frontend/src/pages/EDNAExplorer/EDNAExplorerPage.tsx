import React, { useEffect, useState } from 'react';
import { ednaService } from '../../services/edna';
import { EDNASample, EDNADetection } from '../../types/edna';
import { Card, CardHeader } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Dna, Filter, Sparkles, Activity, FileCode, CheckCircle2 } from 'lucide-react';

export const EDNAExplorerPage: React.FC = () => {
  const [samples, setSamples] = useState<EDNASample[]>([]);
  const [detections, setDetections] = useState<EDNADetection[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadEDNA = async () => {
      setIsLoading(true);
      try {
        const [smps, dets] = await Promise.all([
          ednaService.getSamples(),
          ednaService.getDetections(selectedSampleId !== 'all' ? selectedSampleId : undefined)
        ]);
        setSamples(smps);
        setDetections(dets);
      } catch (err) {
        console.error('Failed to load eDNA data', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadEDNA();
  }, [selectedSampleId]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Dna className="w-5 h-5 text-purple-400" />
            Molecular Environmental DNA (eDNA) Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            High-throughput metabarcoding records from seawater filtration assays targeting teleosts, elasmobranchs, and invertebrates.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="purple" size="md">
            Markers: 12S rRNA / 16S / COI
          </Badge>
          <Badge variant="teal" size="md">
            Illumina NovaSeq Standard
          </Badge>
        </div>
      </div>

      {/* Samples Grid */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Filtration Sampling Stations & Cruise Metadata
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {samples.map((smp) => {
            const isSelected = selectedSampleId === smp.id;
            return (
              <Card
                key={smp.id}
                interactive
                onClick={() => setSelectedSampleId(isSelected ? 'all' : smp.id)}
                className={`p-4 space-y-3 border transition-all ${
                  isSelected
                    ? 'border-purple-500 bg-purple-950/20 shadow-glow-card'
                    : 'border-marine-800 hover:border-purple-400/40'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-xs font-mono font-bold text-white">{smp.sampleCode}</h4>
                    <p className="text-[11px] text-slate-400">{smp.stationId} • {smp.cruiseId}</p>
                  </div>
                  <Badge variant="purple" size="sm">
                    {smp.totalDetectionsCount} Taxa
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="p-1.5 rounded bg-marine-950 border border-marine-850">
                    <span className="text-slate-400 font-sans block text-[9px]">Depth:</span>
                    <span className="text-white font-bold">{smp.samplingDepthMeters}m</span>
                  </div>
                  <div className="p-1.5 rounded bg-marine-950 border border-marine-850">
                    <span className="text-slate-400 font-sans block text-[9px]">DNA Yield:</span>
                    <span className="text-purple-300 font-bold">{smp.dnaYieldNgPerUl} ng/µL</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-1 text-[10px] font-mono">
                  {smp.targetMarkers.map((m) => (
                    <span key={m} className="px-1.5 py-0.5 rounded bg-marine-900 border border-marine-700 text-purple-300">
                      {m}
                    </span>
                  ))}
                  <span className="text-slate-400 ml-auto">{smp.filterType}</span>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Taxonomic Detections Table */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-marine-800 pb-3">
          <div>
            <h3 className="text-sm font-semibold text-white">Taxonomic Sequence Detections & Confidence Ratings</h3>
            <p className="text-xs text-slate-400">
              Matched against MIFish and NCBI BLAST reference databases
            </p>
          </div>

          {selectedSampleId !== 'all' && (
            <button
              onClick={() => setSelectedSampleId('all')}
              className="text-xs text-ocean-cyan hover:underline font-mono"
            >
              Showing filtered sample • Reset to all ({detections.length} total)
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-marine-900/80 border-b border-marine-800 text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                <th className="py-3 px-3">Taxonomic ID & Name</th>
                <th className="py-3 px-3">Common Name</th>
                <th className="py-3 px-3">Marker Gene</th>
                <th className="py-3 px-3">Read Count</th>
                <th className="py-3 px-3">Relative Abundance</th>
                <th className="py-3 px-3">Match Identity</th>
                <th className="py-3 px-3">Confidence Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-marine-850 text-slate-200">
              {detections.map((det) => (
                <tr key={det.id} className="hover:bg-marine-900/50 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white italic">
                    {det.scientificName}
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-300">
                    {det.commonName}
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-purple-950/80 border border-purple-500/40 text-purple-300 text-[10px]">
                      {det.markerUsed}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-ocean-cyan font-bold">
                    {det.readCount.toLocaleString()}
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-marine-950 overflow-hidden border border-marine-800">
                        <div
                          className="h-full bg-ocean-teal rounded-full"
                          style={{ width: `${det.relativeAbundancePercent * 2}%` }}
                        />
                      </div>
                      <span>{det.relativeAbundancePercent}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-emerald-400">
                    {det.matchIdentityPercent}% ({det.referenceDatabase})
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant="teal" size="sm">
                      {(det.confidenceScore * 100).toFixed(0)}% Conf
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
