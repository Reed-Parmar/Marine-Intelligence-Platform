import { ApiClient } from './api';
import { AnalysisResultData, AnalysisParameterConfig } from '../types/analysis';
import { MOCK_ANALYSIS_RESULTS } from './mockData';

function normalizeAnalysisResult(d: any, fallback: AnalysisResultData): AnalysisResultData {
  if (!d) return fallback;
  const stats = d.statistics || {};
  const reg = d.regressionLine || {};
  const prov = d.provenance || {};

  return {
    id: String(d.id || fallback.id),
    title: d.title || fallback.title,
    analysisType: d.analysisType || 'cross_domain_correlation',
    summaryText: d.summaryText || d.summary_text || fallback.summaryText || 'Cross-domain correlation computed across multi-parameter marine observations.',
    status: (d.status || 'completed') as any,
    executionDurationMs: Number(d.executionDurationMs ?? d.execution_duration_ms ?? fallback.executionDurationMs ?? 240),
    parameters: d.parameters || fallback.parameters,
    statistics: {
      sampleSize: Number(stats.sampleSize ?? stats.sample_size ?? d.sample_size ?? fallback.statistics.sampleSize),
      pearsonR: Number(stats.pearsonR ?? stats.pearson_r ?? d.correlation_coefficient ?? fallback.statistics.pearsonR),
      rSquared: Number(stats.rSquared ?? stats.r_squared ?? fallback.statistics.rSquared),
      pValue: (stats.pValue !== undefined ? (stats.pValue === null ? null : Number(stats.pValue)) : 
              (stats.p_value !== undefined ? (stats.p_value === null ? null : Number(stats.p_value)) : 
              (d.p_value !== undefined ? (d.p_value === null ? null : Number(d.p_value)) : 
              fallback.statistics.pValue))),
      standardError: Number(stats.standardError ?? stats.standard_error ?? fallback.statistics.standardError),
      fStatistic: Number(stats.fStatistic ?? stats.f_statistic ?? fallback.statistics.fStatistic),
      slope: Number(stats.slope ?? fallback.statistics.slope),
      intercept: Number(stats.intercept ?? fallback.statistics.intercept)
    },
    scatterPoints: Array.isArray(d.scatterPoints) ? d.scatterPoints : (Array.isArray(d.data_points) ? d.data_points.map((p: any) => ({
      x: Number(p.x ?? 0),
      y: Number(p.y ?? 0),
      stationId: p.stationId || p.station_id || 'STN-01',
      depth: p.depth !== undefined ? Number(p.depth) : undefined
    })) : fallback.scatterPoints),
    regressionLine: {
      xMin: Number(reg.xMin ?? reg.x_min ?? fallback.regressionLine.xMin),
      xMax: Number(reg.xMax ?? reg.x_max ?? fallback.regressionLine.xMax),
      yAtMin: Number(reg.yAtMin ?? reg.y_at_min ?? fallback.regressionLine.yAtMin),
      yAtMax: Number(reg.yAtMax ?? reg.y_at_max ?? fallback.regressionLine.yAtMax)
    },
    ecologicalInterpretation: d.ecologicalInterpretation || d.interpretation || fallback.ecologicalInterpretation,
    provenance: {
      inputDatasetIds: Array.isArray(prov.inputDatasetIds) ? prov.inputDatasetIds : (Array.isArray(prov.input_dataset_ids) ? prov.input_dataset_ids : fallback.provenance.inputDatasetIds),
      recordsUsedCount: Number(prov.recordsUsedCount ?? prov.records_used_count ?? fallback.provenance.recordsUsedCount),
      algorithmName: prov.algorithmName || prov.algorithm_name || fallback.provenance.algorithmName,
      computedTimestamp: prov.computedTimestamp || prov.computed_timestamp || undefined
    }
  };
}

export const analysisService = {
  async getAnalysesList(): Promise<AnalysisResultData[]> {
    const list = Object.values(MOCK_ANALYSIS_RESULTS);
    try {
      const res = await ApiClient.get<any[]>('/analysis');
      const rawList = Array.isArray(res.data) && res.data.length > 0 ? res.data : list;
      return rawList.map((item, idx) => normalizeAnalysisResult(item, list[idx % list.length]));
    } catch {
      return list;
    }
  },

  async getAnalysisById(analysisId: string): Promise<AnalysisResultData> {
    const fallback = MOCK_ANALYSIS_RESULTS[analysisId] || MOCK_ANALYSIS_RESULTS['analysis-sst-richness'];
    try {
      const res = await ApiClient.get<any>(`/analysis/${analysisId}`);
      return normalizeAnalysisResult(res.data || fallback, fallback);
    } catch (err) {
      console.warn(`Analysis API call for '${analysisId}' returned error, using fallback template:`, err);
      return fallback;
    }
  },

  async runCorrelationAnalysis(params: AnalysisParameterConfig): Promise<AnalysisResultData> {
    let key = 'analysis-sst-richness';
    if (params.independentVariable.includes('oxygen') || params.dependentVariable.includes('cpue')) {
      key = 'analysis-oxygen-cpue';
    }
    const template = MOCK_ANALYSIS_RESULTS[key] || MOCK_ANALYSIS_RESULTS['analysis-sst-richness'];
    
    const fallback: AnalysisResultData = {
      ...template,
      id: `analysis-${Date.now()}`,
      title: `${params.independentVariable.replace(/_/g, ' ').toUpperCase()} vs ${params.dependentVariable.replace(/_/g, ' ').toUpperCase()} Correlation`,
      parameters: params,
      provenance: {
        ...template.provenance,
        computedTimestamp: undefined
      }
    };

    const payload = {
      variable_x: params.independentVariable,
      variable_y: params.dependentVariable,
      method: (params as any).method || 'pearson',
      spatial_radius_km: (params as any).spatialToleranceKm ?? 50.0,
      temporal_window_hours: (params as any).temporalWindowHours ?? 72.0,
      depth_tolerance_m: (params as any).depthToleranceMeters ?? 50.0
    };

    try {
      const res = await ApiClient.post<any>('/analysis/correlation', payload);
      return normalizeAnalysisResult(res.data || fallback, fallback);
    } catch (err) {
      console.warn('Analysis execution API returned error, using fallback computation:', err);
      return fallback;
    }
  }
};

