import { ApiClient } from './api';
import {
  DatasetMetadata,
  DatasetQualityReport,
  DatasetProvenance,
  DatasetPreviewData,
  DatasetDomain,
  FileFormat
} from '../types/dataset';

function parseNullableNumber(val: any): number | null {
  if (val === null || val === undefined || val === '') return null;
  const num = Number(val);
  return isNaN(num) ? null : num;
}

function normalizeDataset(d: any): DatasetMetadata {
  return {
    id: String(d.id || ''),
    title: d.title || d.name || 'Untitled Dataset',
    description: d.description || d.validation_notes || 'Marine scientific observation dataset.',
    domain: (d.domain || d.domain_type || 'oceanography') as DatasetDomain,
    format: (d.format || d.file_type || 'TXT').toUpperCase() as FileFormat,
    status: d.status || 'ready',
    qualityStatus: d.qualityStatus || d.quality_status || 'pending',
    qualityScore: d.qualityScore ?? parseNullableNumber(d.quality_score) ?? undefined,
    rowCount: d.rowCount ?? (d.row_count !== undefined ? Number(d.row_count) : 0),
    fileSizeBytes: d.fileSizeBytes ?? (d.file_size_bytes !== undefined ? Number(d.file_size_bytes) : 0),
    source: d.source || d.source_name || '',
    region: d.region || '',
    spatialBounds: d.spatialBounds || d.spatial_bounds,
    temporalCoverage: d.temporalCoverage || d.temporal_coverage || {
      start: d.created_at || '',
      end: d.updated_at || ''
    },
    tags: Array.isArray(d.tags) ? d.tags : (d.domain_type ? [d.domain_type] : []),
    createdAt: d.createdAt || d.created_at || new Date().toISOString(),
    updatedAt: d.updatedAt || d.updated_at || new Date().toISOString(),
    uploadedBy: d.uploadedBy || d.uploaded_by || ''
  };
}

export const datasetService = {
  async getDatasets(params?: { domain?: DatasetDomain; status?: string; search?: string }): Promise<DatasetMetadata[]> {
    const queryParams: Record<string, any> = {};
    if (params?.domain) queryParams.domain_type = params.domain;
    if (params?.status) queryParams.status = params.status;
    if (params?.search) queryParams.search = params.search;

    const res = await ApiClient.get<any>('/datasets', undefined, queryParams);
    // Backend returns ApiListResponse: { data: [...], meta: {...} }
    const raw = res.data;
    const list = Array.isArray(raw) ? raw : (raw?.data && Array.isArray(raw.data) ? raw.data : []);
    return list.map(normalizeDataset);
  },

  async getDatasetById(datasetId: string): Promise<DatasetMetadata> {
    const res = await ApiClient.get<any>(`/datasets/${datasetId}`);
    if (!res.data) throw new Error(`Dataset '${datasetId}' not found.`);
    return normalizeDataset(res.data);
  },

  async getDatasetQuality(datasetId: string): Promise<DatasetQualityReport> {
    const res = await ApiClient.get<any>(`/datasets/${datasetId}/quality`);
    const q = res.data;
    if (!q) throw new Error(`Quality report for dataset '${datasetId}' not found.`);
    return {
      datasetId: q.dataset_id || datasetId,
      score: parseNullableNumber(q.quality_score ?? q.score),
      status: q.quality_status || q.status || 'pending',
      totalRows: parseNullableNumber(q.total_rows ?? q.totalRows) ?? 0,
      validRows: parseNullableNumber(q.valid_rows ?? q.validRows) ?? 0,
      flaggedRows: parseNullableNumber(q.flagged_rows ?? q.flaggedRows) ?? 0,
      duplicateCount: parseNullableNumber(q.duplicate_count ?? q.duplicateCount) ?? 0,
      missingValueRatio: parseNullableNumber(q.missing_value_ratio ?? q.missingValueRatio) ?? 0,
      spatialCompleteness: parseNullableNumber(q.spatialCompleteness ?? q.spatial_completeness),
      temporalCompleteness: parseNullableNumber(q.temporalCompleteness ?? q.temporal_completeness),
      issues: Array.isArray(q.issues) ? q.issues : (q.validation_notes ? [
        {
          id: 'iss-note',
          type: 'info' as const,
          category: 'schema' as const,
          message: q.validation_notes,
          affectedRowsCount: 0
        }
      ] : []),
      computedAt: q.computed_at || q.computedAt || new Date().toISOString()
    };
  },

  async getDatasetProvenance(datasetId: string): Promise<DatasetProvenance> {
    const res = await ApiClient.get<any>(`/datasets/${datasetId}/provenance`);
    const p = res.data;
    if (!p) throw new Error(`Provenance for dataset '${datasetId}' not found.`);
    const meta = p.provenance_metadata || p.provenance || {};
    return {
      datasetId: p.dataset_id || datasetId,
      originalFileName: p.original_file_name || meta.original_filename || (p.storage_file_path ? p.storage_file_path.split('/').pop() : undefined),
      fileHashSha256: p.file_hash_sha256 || meta.file_hash || '',
      sourceInstitution: p.source_institution || meta.source || undefined,
      vesselCruiseId: p.vessel_cruise_id || meta.vessel_cruise_id || undefined,
      uploadedBy: p.uploaded_by || meta.uploaded_by || '',
      uploadedAt: p.uploaded_at || p.created_at || meta.ingested_at || '',
      ingestionPipelineVersion: p.ingestion_pipeline_version || meta.pipeline_version || undefined,
      standardizationRulesApplied: p.standardization_rules_applied || meta.standardization_rules || [],
      storagePath: p.storage_file_path || p.storage_path || meta.storage_path || ''
    };
  },

  async getDatasetPreview(datasetId: string): Promise<DatasetPreviewData> {
    const res = await ApiClient.get<any>(`/datasets/${datasetId}/preview`);
    const prev = res.data;
    if (!prev) throw new Error(`Preview for dataset '${datasetId}' not found.`);
    return {
      datasetId: prev.dataset_id || datasetId,
      columns: Array.isArray(prev.columns)
        ? prev.columns.map((c: any) =>
            typeof c === 'string' ? { name: c, type: 'string' } : { name: c.name || '', type: c.type || 'string', unit: c.unit }
          )
        : [],
      rows: Array.isArray(prev.rows) ? prev.rows : [],
      totalPreviewRows: prev.total_preview_rows !== undefined
        ? Number(prev.total_preview_rows)
        : (Array.isArray(prev.rows) ? prev.rows.length : 0)
    };
  }
};
