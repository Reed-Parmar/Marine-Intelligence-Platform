import { ApiClient } from './api';
import { 
  DatasetMetadata, 
  DatasetQualityReport, 
  DatasetProvenance, 
  DatasetPreviewData,
  DatasetDomain 
} from '../types/dataset';
import { 
  MOCK_DATASETS, 
  MOCK_QUALITY_REPORTS, 
  MOCK_PROVENANCE, 
  MOCK_PREVIEW_DATA 
} from './mockData';

export const datasetService = {
  async getDatasets(params?: { domain?: DatasetDomain; status?: string; search?: string }): Promise<DatasetMetadata[]> {
    let fallback = [...MOCK_DATASETS];
    if (params?.domain) {
      fallback = fallback.filter(d => d.domain === params.domain);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      fallback = fallback.filter(d => 
        d.title.toLowerCase().includes(q) || 
        d.description.toLowerCase().includes(q) ||
        d.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    const res = await ApiClient.get<DatasetMetadata[]>('/datasets', fallback, params);
    return res.data;
  },

  async getDatasetById(datasetId: string): Promise<DatasetMetadata> {
    const fallback = MOCK_DATASETS.find(d => d.id === datasetId) || MOCK_DATASETS[0];
    const res = await ApiClient.get<DatasetMetadata>(`/datasets/${datasetId}`, fallback);
    return res.data;
  },

  async getDatasetQuality(datasetId: string): Promise<DatasetQualityReport> {
    const fallback = MOCK_QUALITY_REPORTS[datasetId] || {
      datasetId,
      score: 95,
      status: 'good',
      totalRows: 4500,
      validRows: 4320,
      flaggedRows: 180,
      duplicateCount: 5,
      missingValueRatio: 0.02,
      spatialCompleteness: 98.0,
      temporalCompleteness: 99.2,
      issues: [
        {
          id: 'iss-def',
          type: 'info',
          category: 'schema',
          message: 'Dataset compliant with CF 1.8 oceanographic standards.',
          affectedRowsCount: 0
        }
      ],
      computedAt: new Date().toISOString()
    };

    const res = await ApiClient.get<DatasetQualityReport>(`/datasets/${datasetId}/quality`, fallback);
    return res.data;
  },

  async getDatasetProvenance(datasetId: string): Promise<DatasetProvenance> {
    const fallback = MOCK_PROVENANCE[datasetId] || {
      datasetId,
      originalFileName: 'dataset_source.txt',
      fileHashSha256: 'a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890',
      sourceInstitution: 'Centre for Marine Living Resources & Ecology (CMLRE)',
      vesselCruiseId: 'FORV Sagar Sampada',
      uploadedBy: 'Dr. Ananya Nair',
      uploadedAt: '2026-08-15T09:20:00Z',
      ingestionPipelineVersion: 'CMLRE-Ingest-v2.4.1',
      standardizationRulesApplied: ['CF Ocean Conventions', 'WGS84 Projection'],
      storagePath: `supabase-storage://cmlre-datasets/${datasetId}`
    };

    const res = await ApiClient.get<DatasetProvenance>(`/datasets/${datasetId}/provenance`, fallback);
    return res.data;
  },

  async getDatasetPreview(datasetId: string): Promise<DatasetPreviewData> {
    const fallback = MOCK_PREVIEW_DATA[datasetId] || MOCK_PREVIEW_DATA['ds-cmlre-txt-01'];
    const res = await ApiClient.get<DatasetPreviewData>(`/datasets/${datasetId}/preview`, fallback);
    return res.data;
  }
};
