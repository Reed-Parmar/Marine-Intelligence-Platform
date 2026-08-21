import { ApiClient } from './api';
import { OceanSummaryMetrics, OceanTrendPoint, CTDProfilePoint } from '../types/ocean';
import { MOCK_OCEAN_SUMMARY, MOCK_OCEAN_TRENDS, MOCK_CTD_DEPTH_CAST } from './mockData';

export const oceanService = {
  async getSummary(): Promise<OceanSummaryMetrics> {
    const res = await ApiClient.get<OceanSummaryMetrics>('/ocean/summary', MOCK_OCEAN_SUMMARY);
    return res.data;
  },

  async getTrends(): Promise<OceanTrendPoint[]> {
    const res = await ApiClient.get<OceanTrendPoint[]>('/ocean/trends', MOCK_OCEAN_TRENDS);
    return res.data;
  },

  async getCTDDepthProfile(stationId?: string): Promise<CTDProfilePoint[]> {
    const res = await ApiClient.get<CTDProfilePoint[]>(
      '/ocean/ctd-profile',
      MOCK_CTD_DEPTH_CAST,
      stationId ? { stationId } : undefined
    );
    return res.data;
  }
};
