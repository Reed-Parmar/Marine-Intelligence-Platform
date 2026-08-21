import { ApiClient } from './api';
import { EDNASample, EDNADetection } from '../types/edna';

function normalizeEDNASample(s: any): EDNASample {
  return {
    id: String(s.id || ''),
    sampleCode: s.sampleCode || s.sample_code || '',
    stationId: s.stationId || s.station_id || '',
    cruiseId: s.cruiseId || s.cruise_id || '',
    samplingDate: s.samplingDate || s.collectionDate || s.collected_at || '',
    latitude: Number(s.latitude ?? 0),
    longitude: Number(s.longitude ?? 0),
    samplingDepthMeters: Number(s.samplingDepthMeters ?? s.depth ?? 0),
    filterType: (s.filterType || s.filter_type || '') as any,
    waterVolumeFilteredLiters: Number(s.waterVolumeFilteredLiters ?? s.water_volume_filtered_liters ?? 0),
    dnaYieldNgPerUl: Number(s.dnaYieldNgPerUl ?? s.dna_yield_ng_per_ul ?? 0),
    targetMarkers: Array.isArray(s.targetMarkers) ? s.targetMarkers : [],
    sequencingPlatform: (s.sequencingPlatform || s.sequencing_platform || '') as any,
    totalDetectionsCount: Number(s.totalDetectionsCount ?? s.total_detections_count ?? s.detected_taxa_count ?? 0),
    collectorName: s.collectorName || s.collector_name || ''
  };
}

function normalizeEDNADetection(d: any): EDNADetection {
  return {
    id: String(d.id || ''),
    sampleId: String(d.sampleId || d.sample_id || ''),
    sampleCode: d.sampleCode || d.sample_code || '',
    speciesId: d.speciesId || d.species_id,
    scientificName: d.scientificName || d.scientific_name || '',
    commonName: d.commonName || d.common_name || '',
    taxonomicRank: (d.taxonomicRank || d.taxonomic_rank || 'Species') as any,
    markerUsed: (d.markerUsed || d.target_marker || '') as any,
    readCount: Number(d.readCount ?? d.read_count ?? 0),
    relativeAbundancePercent: Number(d.relativeAbundancePercent ?? d.relative_abundance_percent ?? 0),
    matchIdentityPercent: Number(d.matchIdentityPercent ?? d.match_identity_percent ?? d.blast_identity_percent ?? 0),
    confidenceScore: Number(d.confidenceScore ?? d.confidence_score ?? 0),
    referenceDatabase: (d.referenceDatabase || d.reference_database || '') as any,
    samplingCoordinates: Array.isArray(d.samplingCoordinates)
      ? d.samplingCoordinates
      : [Number(d.latitude ?? 0), Number(d.longitude ?? 0)]
  };
}

export const ednaService = {
  async getSamples(): Promise<EDNASample[]> {
    const res = await ApiClient.get<any[]>('/edna/samples');
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map(normalizeEDNASample);
  },

  async getSampleById(sampleId: string): Promise<EDNASample> {
    const res = await ApiClient.get<any>(`/edna/samples/${sampleId}`);
    if (!res.data) throw new Error(`eDNA sample '${sampleId}' not found.`);
    return normalizeEDNASample(res.data);
  },

  async getDetections(sampleId?: string): Promise<EDNADetection[]> {
    const res = await ApiClient.get<any[]>(
      '/edna/detections',
      undefined,
      sampleId ? { sample_id: sampleId } : undefined
    );
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map(normalizeEDNADetection);
  }
};
