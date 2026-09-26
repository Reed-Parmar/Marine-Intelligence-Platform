export type MLModelType =
  | 'environmental_anomaly_detector'
  | 'habitat_suitability_maxent'
  | 'catch_forecasting_xgboost'
  | 'biodiversity_risk_classifier'
  | 'marine_species_identification';

export interface MLModelInfo {
  id: string;
  name: string;
  type: MLModelType;
  version: string;
  framework: 'Isolation-Forest' | 'XGBoost' | 'PyTorch' | 'PyTorch ResNet-18' | 'ONNX';
  trainingAccuracyF1: number;
  lastTrainedDate: string;
  inputFeatures: string[];
  description: string;
  status: 'active' | 'retraining' | 'deprecated';
}


export interface AnomalyDetectionResult {
  id: string;
  region: string;
  latitude: number;
  longitude: number;
  detectionDate: string;
  anomalyType: string;
  severity: 'Moderate' | 'High' | 'Severe' | 'Extreme';
  anomalyScore: number; // 0 to 100
  confidenceScore: number; // 0.0 to 1.0
  baselineExpectedValue: string;
  observedCurrentValue: string;
  sst_observed_celsius?: number;
  sst_baseline_celsius?: number;
  sst_anomaly_celsius?: number;
  warm_cold_direction?: 'warm' | 'cold' | 'neutral';
  in_arabian_sea?: boolean;
  subbasin?: string;
  contributingFeatures: {
    feature: string;
    importanceWeight: number; // e.g. 0.45
    impactDirection: 'positive' | 'negative';
  }[];
  mitigationAdvice: string;
}

export interface EnvironmentalAnomalyDetectRequest {
  latitude: number;
  longitude: number;
  sst?: number;
  timestamp?: string;
}


export interface HabitatSuitabilityResult {
  speciesName: string;
  commonName: string;
  targetRegion: string;
  suitabilityIndex: number; // 0.0 - 1.0
  suitabilityClass: 'Optimal' | 'Favorable' | 'Marginal' | 'Unsuitable';
  optimalDepthRangeMeters: [number, number];
  optimalTemperatureRangeCelsius: [number, number];
  predictedBiomassIndex: number;
  confidenceScore: number;
  environmentalDrivers: {
    driver: string;
    currentValue: string;
    optimalRange: string;
    stressContributionPercent: number;
  }[];
}

export interface CatchForecastResult {
  forecastPeriod: string;
  targetSpecies: string;
  predictedCatchTons: number;
  confidenceInterval95: [number, number];
  historicalAverageTons: number;
  trendDirection: 'increasing' | 'stable' | 'declining';
  modelExplanation: string;
}
