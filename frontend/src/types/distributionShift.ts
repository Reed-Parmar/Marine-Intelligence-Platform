/**
 * Type definitions for Seasonal Species Distribution Shift & Movement Propensity Prediction.
 */

export interface Coordinates {
  latitude: floatNumber;
  longitude: floatNumber;
}

export type floatNumber = number;

export interface SeasonInfo {
  season_code: number;
  season_name: string;
}

export interface ForecastInfo {
  source_month: number;
  target_month: number;
  source_season: SeasonInfo;
  target_season: SeasonInfo;
}

export interface SectorPrediction {
  sector: string;
  probability: number;
  centroid?: [number, number];
}

export interface EnvironmentalInputs {
  sst_celsius?: number | null;
  salinity_psu?: number | null;
  dissolved_oxygen_mgl?: number | null;
  chlorophyll_mg_m3?: number | null;
  mean_depth_meters?: number | null;
}

export interface MarkovComparison {
  top_markov_sector: string;
  markov_probability: number;
  fallback_level: number;
  fallback_description: string;
}

export interface ModelMetadata {
  model_version: string;
  training_period: string;
  target_definition: string;
  validation_summary?: {
    shifted_only_top1_accuracy?: number;
    shifted_only_top3_accuracy?: number;
    historical_overall_top1_accuracy?: number;
    historical_overall_top3_accuracy?: number;
    temporal_holdout_top3_accuracy?: number;
  };
  limitations: string[];
}

export interface DistributionShiftPredictionRequest {
  species_id: string;
  current_sector: string;
  latitude: number;
  longitude: number;
  month: number;
  forecast_horizon_months: number;
  mean_depth_meters?: number | null;
  sst_celsius?: number | null;
  salinity_psu?: number | null;
  dissolved_oxygen_mgl?: number | null;
  chlorophyll_mg_m3?: number | null;
}

export interface DistributionShiftPredictionResponse {
  species: string;
  prediction_type: string;
  source_sector: string;
  source_coordinates: Coordinates;
  forecast_horizon_months: number;
  forecast: ForecastInfo;
  top_prediction: SectorPrediction;
  top_3_predictions: SectorPrediction[];
  probability_distribution: Record<string, number>;
  confidence_level: 'HIGH' | 'MODERATE' | 'LOW';
  confidence_tier: string;
  environmental_context_available: boolean;
  environmental_inputs: EnvironmentalInputs;
  markov_baseline_comparison: MarkovComparison;
  model_metadata: ModelMetadata;
  limitations: string[];
}

export const CANONICAL_ARABIAN_SEA_SECTORS: Record<string, [number, number]> = {
  'Malabar Upwelling Shelf': [10.5, 75.5],
  'Central Arabian Sea Offshore Basin': [16.0, 68.0],
  'North Arabian Sea / Gujarat Shelf': [21.5, 69.5],
  'Lakshadweep Sea & Ridge': [10.5, 72.5],
  'Wadge Bank / Comorin Sector': [7.5, 77.5],
  'Konkan Coast / Central West Coast': [16.5, 73.0],
  'South-Eastern Arabian Sea EEZ': [9.0, 76.5],
};

export const SUPPORTED_PRIORITY_SPECIES = [
  { id: 'Sardinella longiceps', name: 'Indian Oil Sardine (Sardinella longiceps)', category: 'Pelagic / Upwelling' },
  { id: 'Rastrelliger kanagurta', name: 'Indian Mackerel (Rastrelliger kanagurta)', category: 'Coastal Pelagic' },
  { id: 'Stolephorus indicus', name: 'Indian Anchovy (Stolephorus indicus)', category: 'Coastal / Estuarine' },
  { id: 'Thunnus albacares', name: 'Yellowfin Tuna (Thunnus albacares)', category: 'Oceanic Pelagic' },
  { id: 'Katsuwonus pelamis', name: 'Skipjack Tuna (Katsuwonus pelamis)', category: 'Oceanic Pelagic' },
  { id: 'Nemipterus japonicus', name: 'Japanese Threadfin Bream (Nemipterus japonicus)', category: 'Demersal' },
  { id: 'Decapterus russelli', name: 'Indian Scad (Decapterus russelli)', category: 'Pelagic' },
  { id: 'Pampus argenteus', name: 'Silver Pomfret (Pampus argenteus)', category: 'Demersal' },
  { id: 'Tenualosa ilisha', name: 'Hilsa Shad (Tenualosa ilisha)', category: 'Anadromous / Pelagic' },
  { id: 'Scomberomorus commerson', name: 'Narrow-barred Spanish Mackerel (Scomberomorus commerson)', category: 'Pelagic Predator' },
];

export const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];
