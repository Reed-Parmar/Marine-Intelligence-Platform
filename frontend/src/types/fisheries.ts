export interface FisheriesObservation {
  id: string;
  tripId: string;
  harborLandingCenter: string;
  state: 'Kerala' | 'Karnataka' | 'Goa' | 'Maharashtra' | 'Tamil Nadu' | 'Andhra Pradesh' | 'Odisha' | 'West Bengal';
  date: string;
  latitude: number;
  longitude: number;
  gearType: 'Trawl net' | 'Gillnet' | 'Purse seine' | 'Hook and line' | 'Longline';
  craftType: 'Mechanized' | 'Motorized' | 'Non-motorized';
  fishingEffortHours: number;
  targetSpeciesGroup: 'Pelagic' | 'Demersal' | 'Crustacean' | 'Molluscan';
  dominantSpeciesName: string;
  catchWeightKg: number;
  cpueKgPerHour: number;
  depthMeters: number;
}

export interface FisheriesTrendPoint {
  period: string;
  pelagicCatchTons: number | null;
  demersalCatchTons: number | null;
  crustaceanCatchTons: number | null;
  averageCPUE: number | null;
  totalEffortHours: number | null;
}

export interface FisheriesSummaryMetrics {
  totalCatchAnnualTons: number | null;
  overallAvgCPUE: number | null;
  activeVesselsTracked: number | null;
  dominantCatchGroup: string | null;
  sustainabilityIndex: number | null;
  topLandingHarbors: {
    name: string;
    landingsTons: number;
  }[];
}

export interface FisheriesCatchPredictionParams {
  Fleet: string;
  Gear: string;
  Effort: number;
  EffortUnits: string;
  Month: number;
  Year: number;
  Latitude: number;
  Longitude: number;
  SpatialResolution?: number;
}

export interface FisheriesCatchPredictionResult {
  predicted_catch: number;
  predicted_catch_mt: number;
  unit: string;
  target_variable: string;
  model: string;
  model_version: string;
  disclaimer: string;
  input_summary: {
    fleet: string;
    gear: string;
    effort: number;
    effort_units: string;
    month: number;
    year: number;
    latitude: number;
    longitude: number;
    season: string;
    log_effort: number;
  };
}

