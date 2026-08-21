import { ApiClient } from './api';
import { EDNASample, EDNADetection } from '../types/edna';
import { MOCK_EDNA_SAMPLES, MOCK_EDNA_DETECTIONS } from './mockData';

export const ednaService = {
  async getSamples(): Promise<EDNASample[]> {
    const res = await ApiClient.get<EDNASample[]>('/edna/samples', MOCK_EDNA_SAMPLES);
    return res.data;
  },

  async getSampleById(sampleId: string): Promise<EDNASample> {
    const fallback = MOCK_EDNA_SAMPLES.find(s => s.id === sampleId) || MOCK_EDNA_SAMPLES[0];
    const res = await ApiClient.get<EDNASample>(`/edna/samples/${sampleId}`, fallback);
    return res.data;
  },

  async getDetections(sampleId?: string): Promise<EDNADetection[]> {
    let fallback = [...MOCK_EDNA_DETECTIONS];
    if (sampleId) {
      fallback = fallback.filter(d => d.sampleId === sampleId);
    }
    const res = await ApiClient.get<EDNADetection[]>(
      '/edna/detections',
      fallback,
      sampleId ? { sampleId } : undefined
    );
    return res.data;
  }
};
