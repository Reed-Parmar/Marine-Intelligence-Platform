import { ApiClient } from './api';
import { MarineAlert, AlertSummaryMetrics } from '../types/alert';
import { MOCK_ALERTS, MOCK_ALERT_SUMMARY } from './mockData';

export const alertsService = {
  async getAlerts(): Promise<MarineAlert[]> {
    const res = await ApiClient.get<MarineAlert[]>('/alerts', MOCK_ALERTS);
    return res.data;
  },

  async getAlertSummary(): Promise<AlertSummaryMetrics> {
    const res = await ApiClient.get<AlertSummaryMetrics>('/alerts/summary', MOCK_ALERT_SUMMARY);
    return res.data;
  },

  async acknowledgeAlert(alertId: string): Promise<MarineAlert> {
    const target = MOCK_ALERTS.find(a => a.id === alertId) || MOCK_ALERTS[0];
    const fallback: MarineAlert = {
      ...target,
      isAcknowledged: true
    };
    const res = await ApiClient.patch<MarineAlert>(`/alerts/${alertId}`, { isAcknowledged: true }, fallback);
    return res.data;
  }
};
