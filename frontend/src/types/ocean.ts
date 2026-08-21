export interface CTDProfilePoint {
  depth: number;
  temperature: number;
  salinity: number;
  dissolvedOxygen: number;
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
  avgSST: number;
  avgSalinity: number;
  avgOxygen: number;
  avgChlorophyll: number;
  anomalyFlag?: boolean;
}

export interface OceanSummaryMetrics {
  meanSST: number;
  minSST: number;
  maxSST: number;
  meanSalinity: number;
  meanOxygen: number;
  hypoxicAreaSqKm: number;
  activeSamplingStations: number;
  totalCTDCasts: number;
}
