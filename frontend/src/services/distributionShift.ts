/**
 * API Service for Seasonal Species Distribution Shift & Movement Propensity Prediction.
 */

import { ApiClient } from './api';
import {
  DistributionShiftPredictionRequest,
  DistributionShiftPredictionResponse,
} from '../types/distributionShift';

export const distributionShiftService = {
  /**
   * Dispatches inference request to backend FastAPI endpoint.
   * Does NOT duplicate ML logic on the client.
   */
  async predictDistributionShift(
    request: DistributionShiftPredictionRequest
  ): Promise<DistributionShiftPredictionResponse> {
    const response = await ApiClient.post<DistributionShiftPredictionResponse>(
      '/distribution-shift/predict',
      request
    );
    return response.data;
  },
};
