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
  pelagicCatchTons: number;
  demersalCatchTons: number;
  crustaceanCatchTons: number;
  averageCPUE: number;
  totalEffortHours: number;
}

export interface FisheriesSummaryMetrics {
  totalCatchAnnualTons: number;
  overallAvgCPUE: number;
  activeVesselsTracked: number;
  dominantCatchGroup: string;
  sustainabilityIndex: number; // 0-100
  topLandingHarbors: {
    name: string;
    landingsTons: number;
  }[];
}
