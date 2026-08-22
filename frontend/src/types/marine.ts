import { DatasetDomain } from './dataset';

export interface MarineObservation {
  id: string;
  datasetId: string;
  domain: DatasetDomain;
  timestamp?: string;
  latitude: number;
  longitude: number;
  depthMeters?: number | null;
  stationId?: string;
  region: 'Arabian Sea' | 'Bay of Bengal' | 'Lakshadweep' | 'Andaman & Nicobar' | 'Indian Ocean';
  
  // Cross-domain values when fused
  temperature?: number; // °C
  salinity?: number; // PSU
  dissolvedOxygen?: number; // mg/L or ml/L
  chlorophyllA?: number; // mg/m³
  ph?: number;
  turbidity?: number;
  
  speciesName?: string;
  scientificName?: string;
  taxonomicGroup?: string;
  individualCount?: number;
  
  catchWeightKg?: number;
  fishingEffortHours?: number;
  gearType?: string;
  vesselType?: string;
  
  ednaDetectionsCount?: number;
  ednaTargetMarker?: string;
  ednaConfidenceScore?: number;
  
  anomalyFlag?: boolean;
  anomalyScore?: number;
  riskLevel?: 'low' | 'moderate' | 'high' | 'critical';
}

export interface MarineSpatialQuery {
  dateFrom?: string;
  dateTo?: string;
  latitude?: number;
  longitude?: number;
  radiusKm?: number;
  bbox?: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]
  depthMin?: number;
  depthMax?: number;
  species?: string;
  domain?: DatasetDomain | 'all';
  datasetId?: string;
  variable?: string;
}

export interface MarineSummary {
  totalObservations: number;
  totalDatasets: number;
  totalSpeciesRecorded: number;
  totalEdnaDetections: number;
  activeAnomalies: number;
  spatialCoveragePercentage: number | null;
  regionsBreakdown: {
    region: string;
    observationCount: number;
    speciesCount: number;
    activeVessels: number;
  }[];
  temporalSpan: {
    earliest: string;
    latest: string;
  } | null;
}

export interface CrossDomainLocationDetail {
  coordinates: {
    latitude: number;
    longitude: number;
  };
  region: string;
  bathymetryDepth: number;
  oceanography: {
    seaSurfaceTemperature: number;
    salinity: number;
    dissolvedOxygen: number;
    chlorophyllA: number;
    thermoclineDepth: number;
    mixedLayerDepth: number;
    lastUpdated: string;
  };
  fisheries: {
    dominantCatch: string;
    totalLandingsTons: number;
    cpueKgPerHour: number;
    dominantGear: string;
    fishingPressureLevel: 'Low' | 'Moderate' | 'High' | 'Very High';
  };
  biodiversity: {
    speciesRecordedCount: number;
    keySpeciesPresent: string[];
    shannonWienerIndex: number;
    endemicSpeciesFlag: boolean;
  };
  molecularEdna: {
    samplesAnalyzed: number;
    taxaIdentified: number;
    topDetections: {
      species: string;
      confidence: number;
      marker: string;
    }[];
  };
  aiPrediction: {
    anomalyDetected: boolean;
    anomalyType?: string;
    riskScore: number;
    habitatSuitabilityPercent: number;
    recommendation: string;
  };
}
