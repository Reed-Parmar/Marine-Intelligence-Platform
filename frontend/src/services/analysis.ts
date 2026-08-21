import { ApiClient } from './api';
import { AnalysisResultData, AnalysisParameterConfig } from '../types/analysis';
import { MOCK_ANALYSIS_RESULTS } from './mockData';

export const analysisService = {
  async getAnalysesList(): Promise<AnalysisResultData[]> {
    const list = Object.values(MOCK_ANALYSIS_RESULTS);
    const res = await ApiClient.get<AnalysisResultData[]>('/analysis', list);
    return res.data;
  },

  async getAnalysisById(analysisId: string): Promise<AnalysisResultData> {
    const fallback = MOCK_ANALYSIS_RESULTS[analysisId] || MOCK_ANALYSIS_RESULTS['analysis-sst-richness'];
    const res = await ApiClient.get<AnalysisResultData>(`/analysis/${analysisId}`, fallback);
    return res.data;
  },

  async runCorrelationAnalysis(params: AnalysisParameterConfig): Promise<AnalysisResultData> {
    // Generate dynamic or matched correlation result
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
        computedTimestamp: new Date().toISOString()
      }
    };

    const res = await ApiClient.post<AnalysisResultData>('/analysis/correlation', params, fallback);
    return res.data;
  }
};
