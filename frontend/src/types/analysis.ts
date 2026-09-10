export type AnalysisType = 
  | 'cross_domain_correlation'
  | 'ocean_trend_analysis'
  | 'fisheries_cpue_trend'
  | 'species_environmental_niche'
  | 'biodiversity_spatial_gradient'
  | 'hypoxia_ecosystem_impact';

export type AnalysisStatus = 'idle' | 'running' | 'completed' | 'failed';

export interface AnalysisParameterConfig {
  analysisType: AnalysisType;
  independentVariable: string; // e.g. 'sea_surface_temperature', 'dissolved_oxygen'
  dependentVariable: string;   // e.g. 'species_richness', 'catch_weight_kg', 'shannon_index'
  region?: string;
  depthMin?: number;
  depthMax?: number;
  dateRange?: [string, string];
  transformation?: 'none' | 'log10' | 'normalize_zscore';
}

export interface CorrelationDataPoint {
  x: number;
  y: number;
  label?: string;
  stationId?: string;
  depth?: number;
  residual?: number;
}

export interface AnalysisResultData {
  id: string;
  title: string;
  analysisType: AnalysisType;
  summaryText: string;
  parameters: AnalysisParameterConfig;
  status: AnalysisStatus;
  executionDurationMs: number;
  statistics: {
    sampleSize: number;
    pearsonR: number;
    rSquared: number;
    pValue: number | null;
    standardError: number;
    fStatistic: number;
    slope: number;
    intercept: number;
  };
  scatterPoints: CorrelationDataPoint[];
  regressionLine: {
    xMin: number;
    xMax: number;
    yAtMin: number;
    yAtMax: number;
  };
  provenance: {
    inputDatasetIds: string[];
    recordsUsedCount: number;
    algorithmName: string;
    computedTimestamp?: string;
  };
  ecologicalInterpretation: string;
}
