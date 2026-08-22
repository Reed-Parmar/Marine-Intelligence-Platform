export interface CTDProfilePoint {
  depth: number;
  temperature: number | null;
  salinity: number | null;
  dissolvedOxygen: number | null;
  chlorophyllA?: number;
  densitySigmaT?: number;
}

export interface OceanObservation {
  id: string;
  stationId: string;
  cruiseId: string;
  vesselName: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  seaSurfaceTemperature: number;
  seaSurfaceSalinity: number;
  dissolvedOxygenSurface: number;
  chlorophyllSurface: number;
  maxDepthSampled: number;
  mixedLayerDepth: number;
  region: string;
  profiles?: CTDProfilePoint[];
}

export interface OceanTrendPoint {
  date: string;
  avgSST: number | null;
  avgSalinity: number | null;
  avgOxygen: number | null;
  avgChlorophyll: number | null;
  anomalyFlag?: boolean;
}

export interface OceanSummaryMetrics {
  meanSST: number | null;
  minSST: number | null;
  maxSST: number | null;
  meanSalinity: number | null;
  meanOxygen: number | null;
  hypoxicAreaSqKm: number | null;
  activeSamplingStations: number | null;
  totalCTDCasts: number | null;
}
