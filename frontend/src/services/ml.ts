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
    try {
      const res = await ApiClient.get<MLModelInfo[]>('/ml/models');
      return res.data || MOCK_ML_MODELS;
    } catch {
      return MOCK_ML_MODELS;
    }
  },

  async getAnomalies(): Promise<AnomalyDetectionResult[]> {
    try {
      const res = await ApiClient.get<AnomalyDetectionResult[]>('/ml/anomalies');
      return res.data || MOCK_ANOMALIES;
    } catch {
      return MOCK_ANOMALIES;
    }
  },

  async getHabitatSuitability(): Promise<HabitatSuitabilityResult[]> {
    try {
      const res = await ApiClient.get<HabitatSuitabilityResult[]>('/ml/habitat-suitability');
      return res.data || MOCK_HABITAT_SUITABILITY;
    } catch {
      return MOCK_HABITAT_SUITABILITY;
    }
  },

  async getCatchForecasts(): Promise<CatchForecastResult[]> {
    try {
      const res = await ApiClient.get<CatchForecastResult[]>('/ml/catch-forecasts');
      return res.data || MOCK_CATCH_FORECASTS;
    } catch {
      return MOCK_CATCH_FORECASTS;
    }
  }
};

