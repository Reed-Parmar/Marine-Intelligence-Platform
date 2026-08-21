import { ApiClient } from './api';
import { OceanSummaryMetrics, OceanTrendPoint, CTDProfilePoint } from '../types/ocean';
import { MOCK_OCEAN_SUMMARY, MOCK_OCEAN_TRENDS, MOCK_CTD_DEPTH_CAST } from './mockData';

export const oceanService = {
  async getSummary(): Promise<OceanSummaryMetrics> {
    const res = await ApiClient.get<any>('/ocean/summary', MOCK_OCEAN_SUMMARY);
    const d = res.data || MOCK_OCEAN_SUMMARY;
    return {
      meanSST: d.meanSST ?? (d.avg_temperature !== undefined ? Number(d.avg_temperature) : 28.4),
      minSST: d.minSST ?? (d.min_temperature !== undefined ? Number(d.min_temperature) : 24.1),
      maxSST: d.maxSST ?? (d.max_temperature !== undefined ? Number(d.max_temperature) : 31.2),
      meanSalinity: d.meanSalinity ?? (d.avg_salinity !== undefined ? Number(d.avg_salinity) : 35.2),
      meanOxygen: d.meanOxygen ?? (d.avg_dissolved_oxygen !== undefined ? Number(d.avg_dissolved_oxygen) : 4.7),
      hypoxicAreaSqKm: d.hypoxicAreaSqKm ?? 120.0,
      activeSamplingStations: d.activeSamplingStations ?? 64,
      totalCTDCasts: d.totalCTDCasts ?? (d.total_observations !== undefined ? Number(d.total_observations) : 1420)
    };
  },

  async getTrends(): Promise<OceanTrendPoint[]> {
    const res = await ApiClient.get<any>('/ocean/trends', MOCK_OCEAN_TRENDS);
    const raw = res.data;
    const items = Array.isArray(raw) ? raw : (raw?.trends && Array.isArray(raw.trends) ? raw.trends : MOCK_OCEAN_TRENDS);
    return items.map((t: any) => ({
      date: String(t.date || t.time_bucket || '2026-01'),
      avgSST: t.avgSST ?? (t.avg_temperature !== undefined ? Number(t.avg_temperature) : 28.0),
      avgSalinity: t.avgSalinity ?? (t.avg_salinity !== undefined ? Number(t.avg_salinity) : 35.0),
      avgOxygen: t.avgOxygen ?? (t.avg_dissolved_oxygen !== undefined ? Number(t.avg_dissolved_oxygen) : 4.5),
      avgChlorophyll: t.avgChlorophyll ?? (t.avg_chlorophyll !== undefined ? Number(t.avg_chlorophyll) : 0.8),
      anomalyFlag: t.anomalyFlag
    }));
  },

  async getCTDDepthProfile(stationId?: string): Promise<CTDProfilePoint[]> {
    const res = await ApiClient.get<any>(
      '/ocean/ctd-profile',
      MOCK_CTD_DEPTH_CAST,
      stationId ? { station_id: stationId } : undefined
    );
    const raw = res.data;
    const list = Array.isArray(raw) ? raw : (raw?.data && Array.isArray(raw.data) ? raw.data : MOCK_CTD_DEPTH_CAST);
    return list.map((p: any) => ({
      depth: Number(p.depth),
      temperature: Number(p.temperature ?? 25.0),
      salinity: Number(p.salinity ?? 35.0),
      dissolvedOxygen: Number(p.dissolvedOxygen ?? p.dissolved_oxygen ?? 4.5),
      chlorophyllA: p.chlorophyllA !== undefined ? Number(p.chlorophyllA) : (p.chlorophyll !== undefined ? Number(p.chlorophyll) : undefined),
      densitySigmaT: p.densitySigmaT !== undefined ? Number(p.densitySigmaT) : undefined
    }));
  }
};
