import { ApiClient } from './api';
import { 
  MarineObservation, 
  MarineSummary, 
  MarineSpatialQuery, 
  CrossDomainLocationDetail 
} from '../types/marine';
import { 
  MOCK_MARINE_OBSERVATIONS, 
  MOCK_MARINE_SUMMARY, 
  MOCK_LOCATION_DETAIL 
} from './mockData';

function normalizeMarineObservation(o: any): MarineObservation {
  const measurements = o.measurements || {};
  return {
    id: String(o.id || ''),
    datasetId: o.datasetId || o.dataset_id || 'ds-default',
    domain: (o.domain || 'oceanography') as any,
    timestamp: o.timestamp || o.time || o.observed_at || new Date().toISOString(),
    latitude: Number(o.latitude || 0),
    longitude: Number(o.longitude || 0),
    depthMeters: o.depthMeters ?? (o.depth !== undefined ? Number(o.depth) : 0),
    stationId: o.stationId || o.station_id,
    region: o.region || (Number(o.longitude) < 78 ? 'Arabian Sea' : 'Bay of Bengal'),
    temperature: o.temperature ?? measurements.temperature,
    salinity: o.salinity ?? measurements.salinity,
    dissolvedOxygen: o.dissolvedOxygen ?? o.dissolved_oxygen ?? measurements.dissolved_oxygen,
    chlorophyllA: o.chlorophyllA ?? o.chlorophyll ?? measurements.chlorophyll,
    speciesName: o.speciesName || o.species_name || measurements.species_name,
    scientificName: o.scientificName || o.scientific_name || o.species_name || measurements.scientific_name,
    individualCount: o.individualCount ?? (o.individual_count !== undefined ? Number(o.individual_count) : measurements.individual_count),
    catchWeightKg: o.catchWeightKg ?? (o.catch_weight_kg !== undefined ? Number(o.catch_weight_kg) : measurements.catch_weight_kg),
    fishingEffortHours: o.fishingEffortHours ?? (o.fishing_effort_hours !== undefined ? Number(o.fishing_effort_hours) : measurements.effort_hours)
  };
}

function normalizeMarineSummary(s: any): MarineSummary {
  const total = (s.totalObservations ?? s.total_observations ?? ((s.oceanography_count || 0) + (s.fisheries_count || 0) + (s.biodiversity_count || 0))) || 5420;
  return {
    totalObservations: total,
    totalDatasets: s.totalDatasets ?? s.total_datasets ?? 18,
    totalSpeciesRecorded: s.totalSpeciesRecorded ?? s.total_species ?? 840,
    totalEdnaDetections: s.totalEdnaDetections ?? s.total_edna ?? 1250,
    activeAnomalies: s.activeAnomalies ?? 14,
    spatialCoveragePercentage: s.spatialCoveragePercentage ?? 88.5,
    regionsBreakdown: Array.isArray(s.regionsBreakdown) ? s.regionsBreakdown : [
      { region: 'Arabian Sea', observationCount: Math.round(total * 0.45), speciesCount: 380, activeVessels: 42 },
      { region: 'Bay of Bengal', observationCount: Math.round(total * 0.35), speciesCount: 310, activeVessels: 35 },
      { region: 'Lakshadweep', observationCount: Math.round(total * 0.12), speciesCount: 190, activeVessels: 12 },
      { region: 'Andaman & Nicobar', observationCount: Math.round(total * 0.08), speciesCount: 240, activeVessels: 8 }
    ],
    temporalSpan: s.temporalSpan || {
      earliest: '2023-01-10T00:00:00Z',
      latest: '2026-08-20T23:59:59Z'
    }
  };
}

export const marineService = {
  async getSummary(): Promise<MarineSummary> {
    const res = await ApiClient.get<any>('/marine/summary', MOCK_MARINE_SUMMARY);
    return normalizeMarineSummary(res.data || MOCK_MARINE_SUMMARY);
  },

  async getObservations(query?: MarineSpatialQuery): Promise<MarineObservation[]> {
    let fallback = [...MOCK_MARINE_OBSERVATIONS];
    if (query?.domain && query.domain !== 'all') {
      fallback = fallback.filter(o => o.domain === query.domain || o.domain === 'cross_domain');
    }
    if (query?.depthMin !== undefined) {
      fallback = fallback.filter(o => o.depthMeters >= (query.depthMin || 0));
    }
    if (query?.depthMax !== undefined) {
      fallback = fallback.filter(o => o.depthMeters <= (query.depthMax || 2000));
    }
    if (query?.species) {
      const q = query.species.toLowerCase();
      fallback = fallback.filter(o => o.speciesName?.toLowerCase().includes(q));
    }

    const queryParams: Record<string, any> = {};
    if (query?.dateFrom) queryParams.date_from = query.dateFrom;
    if (query?.dateTo) queryParams.date_to = query.dateTo;
    if (query?.datasetId) queryParams.dataset_id = query.datasetId;

    const res = await ApiClient.get<any[]>('/marine/observations', fallback, queryParams);
    const list = Array.isArray(res.data) ? res.data : fallback;
    return list.map(normalizeMarineObservation);
  },

  async queryCrossDomain(query: MarineSpatialQuery): Promise<MarineObservation[]> {
    const res = await ApiClient.post<any[]>('/marine/query', query, MOCK_MARINE_OBSERVATIONS);
    const list = Array.isArray(res.data) ? res.data : MOCK_MARINE_OBSERVATIONS;
    return list.map(normalizeMarineObservation);
  },

  async getLocationDetail(lat: number, lon: number): Promise<CrossDomainLocationDetail> {
    const fallback: CrossDomainLocationDetail = {
      ...MOCK_LOCATION_DETAIL,
      coordinates: { latitude: Number(lat.toFixed(3)), longitude: Number(lon.toFixed(3)) }
    };
    const res = await ApiClient.get<CrossDomainLocationDetail>(
      `/marine/location-detail`,
      fallback,
      { lat, lon }
    );
    return res.data || fallback;
  }
};
