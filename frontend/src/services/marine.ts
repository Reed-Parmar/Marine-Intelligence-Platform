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

export const marineService = {
  async getSummary(): Promise<MarineSummary> {
    const res = await ApiClient.get<MarineSummary>('/marine/summary', MOCK_MARINE_SUMMARY);
    return res.data;
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

    const res = await ApiClient.get<MarineObservation[]>('/marine/observations', fallback, query);
    return res.data;
  },

  async queryCrossDomain(query: MarineSpatialQuery): Promise<MarineObservation[]> {
    const res = await ApiClient.post<MarineObservation[]>('/marine/query', query, MOCK_MARINE_OBSERVATIONS);
    return res.data;
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
    return res.data;
  }
};
