export type AlertSeverity = 'critical' | 'warning' | 'advisory' | 'info';
export type AlertCategory = 'biodiversity_risk' | 'environmental_anomaly' | 'fisheries_stress' | 'species_mortality';

export interface MarineAlert {
  id: string;
  title: string;
  category: AlertCategory;
  severity: AlertSeverity;
  region: string;
  latitude: number;
  longitude: number;
  confidencePercent: number;
  timestamp: string;
  isAcknowledged: boolean;
  contributingFactors: {
    factor: string;
    direction: 'up' | 'down' | 'neutral';
    value: string;
  }[];
  description: string;
  affectedSpeciesOrIndustries: string[];
  recommendedAction: string;
}

export interface AlertSummaryMetrics {
  totalAlerts: number;
  criticalCount: number;
  warningCount: number;
  advisoryCount: number;
  unacknowledgedCount: number;
}
