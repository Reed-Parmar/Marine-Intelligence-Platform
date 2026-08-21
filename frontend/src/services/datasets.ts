import { ApiClient } from './api';
import { 
  DatasetMetadata, 
  DatasetQualityReport, 
  DatasetProvenance, 
  DatasetPreviewData,
  DatasetDomain,
  FileFormat 
} from '../types/dataset';
import { 
  MOCK_DATASETS, 
  MOCK_QUALITY_REPORTS, 
  MOCK_PROVENANCE, 
  MOCK_PREVIEW_DATA 
} from './mockData';

function normalizeDataset(d: any): DatasetMetadata {
  return {
    id: String(d.id || ''),
    title: d.title || d.name || 'Untitled Dataset',
    description: d.description || d.validation_notes || 'Marine scientific observation dataset registered in CMLRE repository.',
    domain: (d.domain || d.domain_type || 'oceanography') as DatasetDomain,
    format: (d.format || d.file_type || 'TXT').toUpperCase() as FileFormat,
    status: d.status || 'ready',
    qualityStatus: d.qualityStatus || d.quality_status || 'good',
    qualityScore: d.qualityScore ?? (d.quality_score !== undefined ? Number(d.quality_score) : 95),
    rowCount: d.rowCount ?? (d.row_count !== undefined ? Number(d.row_count) : 0),
    fileSizeBytes: d.fileSizeBytes ?? (d.file_size_bytes !== undefined ? Number(d.file_size_bytes) : 0),
    source: d.source || d.source_name || 'FORV Sagar Sampada',
    region: d.region || 'Indian Ocean',
    spatialBounds: d.spatialBounds || d.spatial_bounds,
    temporalCoverage: d.temporalCoverage || d.temporal_coverage || {
      start: d.created_at || '2025-01-01',
      end: d.updated_at || '2026-08-01'
    },
    tags: Array.isArray(d.tags) ? d.tags : [d.domain_type || 'cmlre', 'postgis'],
    createdAt: d.createdAt || d.created_at || new Date().toISOString(),
    updatedAt: d.updatedAt || d.updated_at || new Date().toISOString(),
    uploadedBy: d.uploadedBy || d.uploaded_by || 'Dr. CMLRE Lead'
  };
}

export const datasetService = {
  async getDatasets(params?: { domain?: DatasetDomain; status?: string; search?: string }): Promise<DatasetMetadata[]> {
    let fallback = [...MOCK_DATASETS];
    if (params?.domain) {
      fallback = fallback.filter(d => d.domain === params.domain);
    }
    if (params?.status) {
      fallback = fallback.filter(d => d.status === params.status);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      fallback = fallback.filter(d => 
        d.title.toLowerCase().includes(q) || 
        d.description.toLowerCase().includes(q) ||
        d.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    const queryParams: Record<string, any> = {};
    if (params?.domain) queryParams.domain_type = params.domain;
    if (params?.status) queryParams.status = params.status;
    if (params?.search) queryParams.search = params.search;

    const res = await ApiClient.get<any[]>('/datasets', fallback, queryParams);
    const list = Array.isArray(res.data) ? res.data : fallback;
    return list.map(normalizeDataset);
  },

  async getDatasetById(datasetId: string): Promise<DatasetMetadata> {
    const fallback = MOCK_DATASETS.find(d => d.id === datasetId) || MOCK_DATASETS[0];
    const res = await ApiClient.get<any>(`/datasets/${datasetId}`, fallback);
    return normalizeDataset(res.data || fallback);
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

    const res = await ApiClient.get<any>(`/datasets/${datasetId}/quality`, fallback);
    const q = res.data || fallback;
    return {
      datasetId: q.datasetId || q.dataset_id || datasetId,
      score: q.score ?? (q.quality_score !== undefined ? Number(q.quality_score) : 95),
      status: q.status || q.quality_status || 'good',
      totalRows: q.totalRows ?? (q.total_rows !== undefined ? Number(q.total_rows) : 1000),
      validRows: q.validRows ?? (q.valid_rows !== undefined ? Number(q.valid_rows) : 980),
      flaggedRows: q.flaggedRows ?? (q.flagged_rows !== undefined ? Number(q.flagged_rows) : 20),
      duplicateCount: q.duplicateCount ?? (q.duplicate_count !== undefined ? Number(q.duplicate_count) : 0),
      missingValueRatio: q.missingValueRatio ?? (q.missing_value_ratio !== undefined ? Number(q.missing_value_ratio) : 0.01),
      spatialCompleteness: q.spatialCompleteness ?? 98.5,
      temporalCompleteness: q.temporalCompleteness ?? 99.1,
      issues: Array.isArray(q.issues) ? q.issues : (q.validation_notes ? [
        {
          id: 'iss-note',
          type: 'info',
          category: 'schema',
          message: q.validation_notes,
          affectedRowsCount: 0
        }
      ] : fallback.issues),
      computedAt: q.computedAt || q.computed_at || new Date().toISOString()
    };
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

    const res = await ApiClient.get<any>(`/datasets/${datasetId}/provenance`, fallback);
    const p = res.data || fallback;
    return {
      datasetId: p.datasetId || p.dataset_id || datasetId,
      originalFileName: p.originalFileName || p.original_file_name || (p.storage_file_path ? p.storage_file_path.split('/').pop() : 'dataset_source.txt'),
      fileHashSha256: p.fileHashSha256 || p.file_hash_sha256 || 'a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890',
      sourceInstitution: p.sourceInstitution || p.source_institution || 'Centre for Marine Living Resources & Ecology (CMLRE)',
      vesselCruiseId: p.vesselCruiseId || p.vessel_cruise_id || 'FORV Sagar Sampada',
      uploadedBy: p.uploadedBy || p.uploaded_by || 'Dr. Ananya Nair',
      uploadedAt: p.uploadedAt || p.uploaded_at || p.created_at || '2026-08-15T09:20:00Z',
      ingestionPipelineVersion: p.ingestionPipelineVersion || p.ingestion_pipeline_version || 'CMLRE-Ingest-v2.4.1',
      standardizationRulesApplied: p.standardizationRulesApplied || p.standardization_rules_applied || ['CF Ocean Conventions', 'WGS84 Projection'],
      storagePath: p.storagePath || p.storage_path || p.storage_file_path || `supabase-storage://cmlre-datasets/${datasetId}`
    };
  },

  async getDatasetPreview(datasetId: string): Promise<DatasetPreviewData> {
    const fallback = MOCK_PREVIEW_DATA[datasetId] || MOCK_PREVIEW_DATA['ds-cmlre-txt-01'];
    const res = await ApiClient.get<any>(`/datasets/${datasetId}/preview`, fallback);
    const prev = res.data || fallback;
    return {
      datasetId: prev.datasetId || prev.dataset_id || datasetId,
      columns: Array.isArray(prev.columns) ? prev.columns.map((c: any) => typeof c === 'string' ? { name: c, type: 'string' } : { name: c.name || '', type: c.type || 'string', unit: c.unit }) : fallback.columns,
      rows: Array.isArray(prev.rows) ? prev.rows : fallback.rows,
      totalPreviewRows: prev.totalPreviewRows ?? (prev.total_preview_rows !== undefined ? Number(prev.total_preview_rows) : (prev.rows ? prev.rows.length : fallback.totalPreviewRows))
    };
  }
};
