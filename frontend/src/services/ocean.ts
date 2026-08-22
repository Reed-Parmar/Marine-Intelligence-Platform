import { ApiClient } from './api';
import { OceanSummaryMetrics, OceanTrendPoint, CTDProfilePoint } from '../types/ocean';

export const oceanService = {
  async getSummary(): Promise<OceanSummaryMetrics> {
    const res = await ApiClient.get<any>('/ocean/summary');
    const d = res.data || {};
    return {
      meanSST: d.meanSST ?? (d.avg_temperature !== undefined ? Number(d.avg_temperature) : null),
      minSST: d.minSST ?? (d.min_temperature !== undefined ? Number(d.min_temperature) : null),
      maxSST: d.maxSST ?? (d.max_temperature !== undefined ? Number(d.max_temperature) : null),
      meanSalinity: d.meanSalinity ?? (d.avg_salinity !== undefined ? Number(d.avg_salinity) : null),
      meanOxygen: d.meanOxygen ?? (d.avg_dissolved_oxygen !== undefined ? Number(d.avg_dissolved_oxygen) : null),
      hypoxicAreaSqKm: d.hypoxicAreaSqKm ?? null,
      activeSamplingStations: d.activeSamplingStations ?? null,
      totalCTDCasts: d.totalCTDCasts ?? (d.total_observations !== undefined ? Number(d.total_observations) : null)
    };
  },

  async getTrends(): Promise<OceanTrendPoint[]> {
    const res = await ApiClient.get<any>('/ocean/trends');
    const raw = res.data;
    const items = Array.isArray(raw) ? raw : (raw?.trends && Array.isArray(raw.trends) ? raw.trends : []);
    return items.map((t: any) => ({
      date: String(t.date || t.time_bucket || ''),
      avgSST: t.avgSST ?? (t.avg_temperature !== undefined ? Number(t.avg_temperature) : null),
      avgSalinity: t.avgSalinity ?? (t.avg_salinity !== undefined ? Number(t.avg_salinity) : null),
      avgOxygen: t.avgOxygen ?? (t.avg_dissolved_oxygen !== undefined ? Number(t.avg_dissolved_oxygen) : null),
      avgChlorophyll: t.avgChlorophyll ?? (t.avg_chlorophyll !== undefined ? Number(t.avg_chlorophyll) : null),
      anomalyFlag: t.anomalyFlag
    }));
  },

  async getCTDDepthProfile(stationId?: string): Promise<CTDProfilePoint[]> {
    const res = await ApiClient.get<any>(
      '/ocean/ctd-profile',
      undefined,
      stationId ? { station_id: stationId } : undefined
    );
    const raw = res.data;
    const list = Array.isArray(raw) ? raw : (raw?.data && Array.isArray(raw.data) ? raw.data : []);
    return list.map((p: any) => ({
      depth: Number(p.depth),
      temperature: p.temperature !== undefined ? Number(p.temperature) : null,
      salinity: p.salinity !== undefined ? Number(p.salinity) : null,
      dissolvedOxygen: p.dissolvedOxygen !== undefined ? Number(p.dissolvedOxygen) : (p.dissolved_oxygen !== undefined ? Number(p.dissolved_oxygen) : null),
      chlorophyllA: p.chlorophyllA !== undefined ? Number(p.chlorophyllA) : (p.chlorophyll !== undefined ? Number(p.chlorophyll) : undefined),
      densitySigmaT: p.densitySigmaT !== undefined ? Number(p.densitySigmaT) : undefined
    }));
  }
};
