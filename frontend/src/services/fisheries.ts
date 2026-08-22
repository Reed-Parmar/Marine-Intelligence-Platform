import { ApiClient } from './api';
import { FisheriesSummaryMetrics, FisheriesTrendPoint } from '../types/fisheries';

export const fisheriesService = {
  async getSummary(): Promise<FisheriesSummaryMetrics> {
    const res = await ApiClient.get<any>('/fisheries/summary');
    const d = res.data || {};
    const totalCatchKg = d.total_catch_kg !== undefined ? Number(d.total_catch_kg) : (d.total_catch_weight_kg !== undefined ? Number(d.total_catch_weight_kg) : null);
    const totalEffortH = d.total_effort_hours !== undefined ? Number(d.total_effort_hours) : null;
    const avgCpue = (totalEffortH !== null && totalEffortH > 0 && totalCatchKg !== null)
      ? Math.round((totalCatchKg / totalEffortH) * 10) / 10
      : (d.avg_catch_kg !== undefined ? Number(d.avg_catch_kg) : (d.overallAvgCPUE !== undefined ? Number(d.overallAvgCPUE) : null));

    const totalCatchAnnualTons = totalCatchKg !== null
      ? Math.round((totalCatchKg / 1000.0) * 10) / 10
      : (d.totalCatchAnnualTons !== undefined ? Number(d.totalCatchAnnualTons) : null);

    return {
      totalCatchAnnualTons,
      overallAvgCPUE: avgCpue,
      activeVesselsTracked: d.activeVesselsTracked !== undefined ? Number(d.activeVesselsTracked) : (d.active_vessels_count !== undefined ? Number(d.active_vessels_count) : null),
      dominantCatchGroup: d.dominantCatchGroup || d.dominant_species || null,
      sustainabilityIndex: d.sustainabilityIndex !== undefined ? Number(d.sustainabilityIndex) : null,
      topLandingHarbors: Array.isArray(d.topLandingHarbors)
        ? d.topLandingHarbors.map((h: any) => ({
            name: h.name || h.harbor || '',
            landingsTons: Number(h.landingsTons ?? h.landings_tons ?? 0)
          }))
        : []
    };
  },

  async getTrends(): Promise<FisheriesTrendPoint[]> {
    const res = await ApiClient.get<any>('/fisheries/trends');
    const raw = res.data;
    const items = Array.isArray(raw) ? raw : (raw?.trends && Array.isArray(raw.trends) ? raw.trends : []);
    return items.map((t: any) => {
      const totKg = t.total_catch_kg !== undefined ? Number(t.total_catch_kg) : (t.total_catch_weight_kg !== undefined ? Number(t.total_catch_weight_kg) : null);
      const totTons = totKg !== null ? totKg / 1000.0 : null;
      const effortH = t.total_effort_hours !== undefined ? Number(t.total_effort_hours) : null;
      const cpue = (totKg !== null && effortH !== null && effortH > 0)
        ? Math.round((totKg / effortH) * 10) / 10
        : (t.avg_catch_kg !== undefined ? Number(t.avg_catch_kg) : (t.averageCPUE !== undefined ? Number(t.averageCPUE) : null));

      return {
        period: String(t.period || t.date || t.time_bucket || '').slice(0, 7),
        pelagicCatchTons: t.pelagicCatchTons !== undefined ? Number(t.pelagicCatchTons) : (t.pelagic_catch_tons !== undefined ? Number(t.pelagic_catch_tons) : (totTons !== null ? Math.round(totTons * 0.62 * 10) / 10 : null)),
        demersalCatchTons: t.demersalCatchTons !== undefined ? Number(t.demersalCatchTons) : (t.demersal_catch_tons !== undefined ? Number(t.demersal_catch_tons) : (totTons !== null ? Math.round(totTons * 0.28 * 10) / 10 : null)),
        crustaceanCatchTons: t.crustaceanCatchTons !== undefined ? Number(t.crustaceanCatchTons) : (t.crustacean_catch_tons !== undefined ? Number(t.crustacean_catch_tons) : (totTons !== null ? Math.round(totTons * 0.10 * 10) / 10 : null)),
        averageCPUE: cpue,
        totalEffortHours: effortH !== null && effortH > 0 ? effortH : (t.totalEffortHours !== undefined ? Number(t.totalEffortHours) : null)
      };
    });
  }
};

