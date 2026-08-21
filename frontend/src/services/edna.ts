import { ApiClient } from './api';
import { EDNASample, EDNADetection } from '../types/edna';
import { MOCK_EDNA_SAMPLES, MOCK_EDNA_DETECTIONS } from './mockData';

function normalizeEDNASample(s: any): EDNASample {
  return {
    id: String(s.id || ''),
    sampleCode: s.sampleCode || s.sample_code || 'eDNA-STN-01',
    stationId: s.stationId || s.station_id || 'STN-AS-01',
    cruiseId: s.cruiseId || s.cruise_id || 'SS-412',
    samplingDate: s.samplingDate || s.collectionDate || s.collected_at || new Date().toISOString(),
    latitude: Number(s.latitude || 0),
    longitude: Number(s.longitude || 0),
    samplingDepthMeters: Number(s.samplingDepthMeters ?? s.depth ?? 10),
    filterType: (s.filterType || s.filter_type || 'Sterivex 0.22µm') as any,
    waterVolumeFilteredLiters: Number(s.waterVolumeFilteredLiters ?? s.water_volume_filtered_liters ?? 2.5),
    dnaYieldNgPerUl: Number(s.dnaYieldNgPerUl ?? s.dna_yield_ng_per_ul ?? 18.5),
    targetMarkers: Array.isArray(s.targetMarkers) ? s.targetMarkers : ['12S', '16S'],
    sequencingPlatform: (s.sequencingPlatform || s.sequencing_platform || 'Illumina NovaSeq') as any,
    totalDetectionsCount: Number(s.totalDetectionsCount ?? s.total_detections_count ?? s.detected_taxa_count ?? 24),
    collectorName: s.collectorName || s.collector_name || 'CMLRE Marine Genomics Lab'
  };
}

function normalizeEDNADetection(d: any): EDNADetection {
  return {
    id: String(d.id || ''),
    sampleId: String(d.sampleId || d.sample_id || ''),
    sampleCode: d.sampleCode || d.sample_code || 'CMLRE-412-STN01-D25',
    speciesId: d.speciesId || d.species_id,
    scientificName: d.scientificName || d.scientific_name || 'Pelagic taxon',
    commonName: d.commonName || d.common_name || 'Marine species',
    taxonomicRank: (d.taxonomicRank || d.taxonomic_rank || 'Species') as any,
    markerUsed: (d.markerUsed || d.target_marker || '12S') as any,
    readCount: Number(d.readCount ?? d.read_count ?? 540),
    relativeAbundancePercent: Number(d.relativeAbundancePercent ?? d.relative_abundance_percent ?? 4.2),
    matchIdentityPercent: Number(d.matchIdentityPercent ?? d.match_identity_percent ?? d.blast_identity_percent ?? 99.4),
    confidenceScore: Number(d.confidenceScore ?? d.confidence_score ?? 0.98),
    referenceDatabase: (d.referenceDatabase || d.reference_database || 'MIFish') as any,
    samplingCoordinates: Array.isArray(d.samplingCoordinates) ? d.samplingCoordinates : [Number(d.latitude ?? 9.94), Number(d.longitude ?? 75.82)]
  };
}

export const ednaService = {
  async getSamples(): Promise<EDNASample[]> {
    const res = await ApiClient.get<any[]>('/edna/samples', MOCK_EDNA_SAMPLES);
    const list = Array.isArray(res.data) ? res.data : MOCK_EDNA_SAMPLES;
    return list.map(normalizeEDNASample);
  },

  async getSampleById(sampleId: string): Promise<EDNASample> {
    const fallback = MOCK_EDNA_SAMPLES.find(s => s.id === sampleId) || MOCK_EDNA_SAMPLES[0];
    const res = await ApiClient.get<any>(`/edna/samples/${sampleId}`, fallback);
    return normalizeEDNASample(res.data || fallback);
  },

  async getDetections(sampleId?: string): Promise<EDNADetection[]> {
    let fallback = [...MOCK_EDNA_DETECTIONS];
    if (sampleId) {
      fallback = fallback.filter(d => d.sampleId === sampleId);
    }
    const res = await ApiClient.get<any[]>(
      '/edna/detections',
      fallback,
      sampleId ? { sample_id: sampleId } : undefined
    );
    const list = Array.isArray(res.data) ? res.data : fallback;
    return list.map(normalizeEDNADetection);
  }
};
