import { ApiClient } from './api';
import { 
  MLModelInfo, 
  AnomalyDetectionResult, 
  HabitatSuitabilityResult, 
  CatchForecastResult 
} from '../types/ml';
import { 
  MOCK_ML_MODELS, 
  MOCK_ANOMALIES, 
  MOCK_HABITAT_SUITABILITY, 
  MOCK_CATCH_FORECASTS 
} from './mockData';

export const mlService = {
  async getModels(): Promise<MLModelInfo[]> {
    const res = await ApiClient.get<MLModelInfo[]>('/ml/models', MOCK_ML_MODELS);
    return res.data;
  },

  async getAnomalies(): Promise<AnomalyDetectionResult[]> {
    const res = await ApiClient.get<AnomalyDetectionResult[]>('/ml/anomalies', MOCK_ANOMALIES);
    return res.data;
  },

  async getHabitatSuitability(): Promise<HabitatSuitabilityResult[]> {
    const res = await ApiClient.get<HabitatSuitabilityResult[]>('/ml/habitat-suitability', MOCK_HABITAT_SUITABILITY);
    return res.data;
  },

  async getCatchForecasts(): Promise<CatchForecastResult[]> {
    const res = await ApiClient.get<CatchForecastResult[]>('/ml/catch-forecasts', MOCK_CATCH_FORECASTS);
    return res.data;
  }
};
