import { ApiClient } from './api';
import { MarineAlert, AlertSummaryMetrics } from '../types/alert';

function normalizeAlert(a: any): MarineAlert {
  return {
    id: String(a.id || ''),
    title: a.title || 'Marine Alert',
    category: (a.category || a.alert_type || 'environmental_anomaly') as any,
    severity: (a.severity || 'warning') as any,
    region: a.region || '',
    latitude: Number(a.latitude ?? a.coordinates?.latitude ?? 0),
    longitude: Number(a.longitude ?? a.coordinates?.longitude ?? 0),
    confidencePercent: Number(a.confidencePercent ?? a.confidence_percent ?? 0),
    timestamp: a.timestamp || a.created_at || new Date().toISOString(),
    isAcknowledged: a.isAcknowledged ?? (a.status === 'acknowledged' || a.status === 'resolved' || a.is_acknowledged === true),
    contributingFactors: Array.isArray(a.contributingFactors) ? a.contributingFactors : [],
    description: a.description || a.message || '',
    affectedSpeciesOrIndustries: Array.isArray(a.affectedSpeciesOrIndustries) ? a.affectedSpeciesOrIndustries : [],
    recommendedAction: a.recommendedAction || a.suggested_action || ''
  };
}

function normalizeAlertSummary(s: any): AlertSummaryMetrics {
  return {
    totalAlerts: Number(s.totalAlerts ?? s.total_alerts ?? 0),
    criticalCount: Number(s.criticalCount ?? s.critical_count ?? 0),
    warningCount: Number(s.warningCount ?? s.warning_count ?? 0),
    advisoryCount: Number(s.advisoryCount ?? s.advisory_count ?? 0),
    unacknowledgedCount: Number(s.unacknowledgedCount ?? s.unacknowledged_count ?? 0)
  };
}

export const alertsService = {
  async getAlerts(): Promise<MarineAlert[]> {
    const res = await ApiClient.get<any[]>('/alerts');
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map(normalizeAlert);
  },

  async getAlertSummary(): Promise<AlertSummaryMetrics> {
    const res = await ApiClient.get<any>('/alerts/summary');
    return normalizeAlertSummary(res.data || {});
  },

  async acknowledgeAlert(alertId: string): Promise<MarineAlert> {
    const res = await ApiClient.patch<any>(`/alerts/${alertId}`, { isAcknowledged: true });
    if (!res.data) throw new Error(`Alert '${alertId}' not found or could not be acknowledged.`);
    return normalizeAlert(res.data);
  }
};
