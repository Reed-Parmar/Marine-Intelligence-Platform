import { ApiClient } from './api';
import { FisheriesSummaryMetrics, FisheriesTrendPoint } from '../types/fisheries';
import { MOCK_FISHERIES_SUMMARY, MOCK_FISHERIES_TRENDS } from './mockData';

export const fisheriesService = {
  async getSummary(): Promise<FisheriesSummaryMetrics> {
    const res = await ApiClient.get<any>('/fisheries/summary', MOCK_FISHERIES_SUMMARY);
    const d = res.data || MOCK_FISHERIES_SUMMARY;
    return {
      totalCatchAnnualTons: Number(d.totalCatchAnnualTons ?? (d.total_catch_weight_kg !== undefined ? Number(d.total_catch_weight_kg) / 1000.0 : 285400)),
      overallAvgCPUE: Number(d.overallAvgCPUE ?? (d.avg_catch_per_trip_kg !== undefined ? Number(d.avg_catch_per_trip_kg) : 148)),
      activeVesselsTracked: Number(d.activeVesselsTracked ?? (d.active_vessels_count !== undefined ? Number(d.active_vessels_count) : 2340)),
      dominantCatchGroup: d.dominantCatchGroup || d.dominant_species || 'Pelagic (Sardines & Mackerel)',
      sustainabilityIndex: Number(d.sustainabilityIndex ?? 74),
      topLandingHarbors: Array.isArray(d.topLandingHarbors) ? d.topLandingHarbors : [
        { name: 'Kochi Harbour', landingsTons: 62400 },
        { name: 'Mangalore Port', landingsTons: 51200 }
      ]
    };
  },

  async getTrends(): Promise<FisheriesTrendPoint[]> {
    const res = await ApiClient.get<any>('/fisheries/trends', MOCK_FISHERIES_TRENDS);
    const raw = res.data;
    const items = Array.isArray(raw) ? raw : (raw?.trends && Array.isArray(raw.trends) ? raw.trends : MOCK_FISHERIES_TRENDS);
    return items.map((t: any) => ({
      period: String(t.period || t.date || t.time_bucket || 'Q1 2024'),
      pelagicCatchTons: Number(t.pelagicCatchTons ?? (t.total_catch_weight_kg !== undefined ? Number(t.total_catch_weight_kg) / 2000.0 : 52000)),
      demersalCatchTons: Number(t.demersalCatchTons ?? 28000),
      crustaceanCatchTons: Number(t.crustaceanCatchTons ?? 14000),
      averageCPUE: Number(t.averageCPUE ?? (t.cpue_kg_per_hour !== undefined ? Number(t.cpue_kg_per_hour) : 135)),
      totalEffortHours: Number(t.totalEffortHours ?? (t.total_effort_hours !== undefined ? Number(t.total_effort_hours) : 72000))
    }));
  }
};
