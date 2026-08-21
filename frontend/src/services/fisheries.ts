import { ApiClient } from './api';
import { FisheriesSummaryMetrics, FisheriesTrendPoint } from '../types/fisheries';

export const fisheriesService = {
  async getSummary(): Promise<FisheriesSummaryMetrics> {
    const res = await ApiClient.get<any>('/fisheries/summary');
    const d = res.data || {};
    return {
      totalCatchAnnualTons: d.totalCatchAnnualTons !== undefined
        ? Number(d.totalCatchAnnualTons)
        : (d.total_catch_weight_kg !== undefined ? Number(d.total_catch_weight_kg) / 1000.0 : null),
      overallAvgCPUE: d.overallAvgCPUE !== undefined
        ? Number(d.overallAvgCPUE)
        : (d.avg_catch_per_trip_kg !== undefined ? Number(d.avg_catch_per_trip_kg) : null),
      activeVesselsTracked: d.activeVesselsTracked !== undefined
        ? Number(d.activeVesselsTracked)
        : (d.active_vessels_count !== undefined ? Number(d.active_vessels_count) : null),
      dominantCatchGroup: d.dominantCatchGroup || d.dominant_species || null,
      sustainabilityIndex: d.sustainabilityIndex !== undefined ? Number(d.sustainabilityIndex) : null,
      topLandingHarbors: Array.isArray(d.topLandingHarbors) ? d.topLandingHarbors : []
    };
  },

  async getTrends(): Promise<FisheriesTrendPoint[]> {
    const res = await ApiClient.get<any>('/fisheries/trends');
    const raw = res.data;
    const items = Array.isArray(raw) ? raw : (raw?.trends && Array.isArray(raw.trends) ? raw.trends : []);
    return items.map((t: any) => ({
      period: String(t.period || t.date || t.time_bucket || ''),
      pelagicCatchTons: t.pelagicCatchTons !== undefined
        ? Number(t.pelagicCatchTons)
        : (t.total_catch_weight_kg !== undefined ? Number(t.total_catch_weight_kg) / 1000.0 : null),
      demersalCatchTons: t.demersalCatchTons !== undefined ? Number(t.demersalCatchTons) : null,
      crustaceanCatchTons: t.crustaceanCatchTons !== undefined ? Number(t.crustaceanCatchTons) : null,
      averageCPUE: t.averageCPUE !== undefined
        ? Number(t.averageCPUE)
        : (t.cpue_kg_per_hour !== undefined ? Number(t.cpue_kg_per_hour) : null),
      totalEffortHours: t.totalEffortHours !== undefined
        ? Number(t.totalEffortHours)
        : (t.total_effort_hours !== undefined ? Number(t.total_effort_hours) : null)
    }));
  }
};
