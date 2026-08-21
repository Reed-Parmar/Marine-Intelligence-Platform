import { ApiClient } from './api';
import { MarineAlert, AlertSummaryMetrics } from '../types/alert';
import { MOCK_ALERTS, MOCK_ALERT_SUMMARY } from './mockData';

function normalizeAlert(a: any): MarineAlert {
  return {
    id: String(a.id || ''),
    title: a.title || 'Marine Ecological Anomaly',
    category: (a.category || a.alert_type || 'environmental_anomaly') as any,
    severity: (a.severity || 'warning') as any,
    region: a.region || 'South-Eastern Arabian Sea',
    latitude: Number(a.latitude ?? a.coordinates?.latitude ?? 10.5),
    longitude: Number(a.longitude ?? a.coordinates?.longitude ?? 75.2),
    confidencePercent: Number(a.confidencePercent ?? a.confidence_percent ?? 85),
    timestamp: a.timestamp || a.created_at || new Date().toISOString(),
    isAcknowledged: a.isAcknowledged ?? (a.status === 'acknowledged' || a.status === 'resolved' || a.is_acknowledged === true),
    contributingFactors: Array.isArray(a.contributingFactors) ? a.contributingFactors : [
      { factor: 'Dissolved Oxygen (DO)', direction: 'down', value: `${a.current_value ?? 1.9} mg/L` },
      { factor: 'SST Variance', direction: 'up', value: '+1.2°C' }
    ],
    description: a.description || a.message || 'Environmental parameter threshold variance detected.',
    affectedSpeciesOrIndustries: Array.isArray(a.affectedSpeciesOrIndustries) ? a.affectedSpeciesOrIndustries : ['Demersal Fisheries', 'Pelagic Schools'],
    recommendedAction: a.recommendedAction || a.suggested_action || 'Deploy CTD casts and monitor adjacent hydrographic stations.'
  };
}

function normalizeAlertSummary(s: any): AlertSummaryMetrics {
  return {
    totalAlerts: Number(s.totalAlerts ?? s.total_alerts ?? 3),
    criticalCount: Number(s.criticalCount ?? s.critical_count ?? 1),
    warningCount: Number(s.warningCount ?? s.warning_count ?? 1),
    advisoryCount: Number(s.advisoryCount ?? s.advisory_count ?? 1),
    unacknowledgedCount: Number(s.unacknowledgedCount ?? s.unacknowledged_count ?? 2)
  };
}

export const alertsService = {
  async getAlerts(): Promise<MarineAlert[]> {
    const res = await ApiClient.get<any[]>('/alerts', MOCK_ALERTS);
    const list = Array.isArray(res.data) ? res.data : MOCK_ALERTS;
    return list.map(normalizeAlert);
  },

  async getAlertSummary(): Promise<AlertSummaryMetrics> {
    const res = await ApiClient.get<any>('/alerts/summary', MOCK_ALERT_SUMMARY);
    return normalizeAlertSummary(res.data || MOCK_ALERT_SUMMARY);
  },

  async acknowledgeAlert(alertId: string): Promise<MarineAlert> {
    const target = MOCK_ALERTS.find(a => a.id === alertId) || MOCK_ALERTS[0];
    const fallback: MarineAlert = {
      ...target,
      isAcknowledged: true
    };
    const res = await ApiClient.patch<any>(`/alerts/${alertId}`, { isAcknowledged: true }, fallback);
    return normalizeAlert(res.data || fallback);
  }
};
