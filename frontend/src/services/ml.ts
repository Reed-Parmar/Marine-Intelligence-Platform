import { ApiClient } from './api';
import { 
  MLModelInfo, 
  AnomalyDetectionResult, 
  HabitatSuitabilityResult, 
  CatchForecastResult 
} from '../types/ml';
import { 
  MOCK_ML_MODELS, 
  MOCK_HABITAT_SUITABILITY, 
  MOCK_CATCH_FORECASTS 
} from './mockData';

export const mlService = {
  async getModels(): Promise<MLModelInfo[]> {
    try {
      const res = await ApiClient.get<any[]>('/ml/models');
      const rawList = Array.isArray(res.data) ? res.data : [];
      if (rawList.length > 0) {
        return rawList.map((m: any) => ({
          id: m.model_id || m.id || 'ml-mod',
          name: m.name,
          type: m.task_type || m.type || 'environmental_anomaly_detector',
          version: m.version || '1.0.0',
          framework: (m.metrics?.algorithm as any) || m.framework || 'Isolation-Forest',
          trainingAccuracyF1: typeof m.metrics?.unsupervised_anomaly_rate_pct === 'number'
            ? m.metrics.unsupervised_anomaly_rate_pct / 100
            : (typeof m.trainingAccuracyF1 === 'number' ? m.trainingAccuracyF1 : 0.95),
          lastTrainedDate: m.metrics?.test_period || m.lastTrainedDate || '2025 (held-out)',
          inputFeatures: Array.isArray(m.input_features)
            ? m.input_features
            : (Array.isArray(m.inputFeatures) ? m.inputFeatures : []),
          description: m.description || `${m.name} — Deployed production inference model.`,
          status: m.status || 'active'
        }));
      }
      return [];
    } catch (err) {
      console.warn('Failed to load ML models from backend', err);
      return [];
    }
  },

  async getAnomalies(): Promise<AnomalyDetectionResult[]> {
    // Environmental Anomaly V2 must NOT use MOCK_ANOMALIES as silent fallback.
    const res = await ApiClient.get<AnomalyDetectionResult[]>('/ml/anomalies');
    return res.data || [];
  },

  async detectEnvironmentalAnomaly(params: {
    latitude: number;
    longitude: number;
    sst?: number;
    timestamp?: string;
  }): Promise<AnomalyDetectionResult> {
    const res = await ApiClient.post<AnomalyDetectionResult>('/ml/anomalies/detect', params);
    return res.data;
  },

  async getEnvironmentalAnomalyModelInfo(): Promise<any> {
    const res = await ApiClient.get<any>('/ml/environmental-anomaly/model-info');
    return res.data;
  },

  async getHabitatSuitability(): Promise<HabitatSuitabilityResult[]> {
    // Unimplemented on backend; return empty state directly to avoid obsolete 404 network requests
    return [];
  },

  async getCatchForecasts(): Promise<CatchForecastResult[]> {
    // Legacy MBLF-Net mock forecasts disabled per requirement; return empty state directly to avoid obsolete 404 network requests
    return [];
  }
};

