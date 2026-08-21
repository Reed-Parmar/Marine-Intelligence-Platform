import { ApiClient } from './api';
import { FisheriesSummaryMetrics, FisheriesTrendPoint } from '../types/fisheries';
import { MOCK_FISHERIES_SUMMARY, MOCK_FISHERIES_TRENDS } from './mockData';

export const fisheriesService = {
  async getSummary(): Promise<FisheriesSummaryMetrics> {
    const res = await ApiClient.get<FisheriesSummaryMetrics>('/fisheries/summary', MOCK_FISHERIES_SUMMARY);
    return res.data;
  },

  async getTrends(): Promise<FisheriesTrendPoint[]> {
    const res = await ApiClient.get<FisheriesTrendPoint[]>('/fisheries/trends', MOCK_FISHERIES_TRENDS);
    return res.data;
  }
};
