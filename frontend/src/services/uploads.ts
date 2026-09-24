import { ApiClient } from './api';
import { DatasetUploadResponse, FileFormat } from '../types/dataset';

function normalizeUploadResponse(d: any): DatasetUploadResponse {
  return {
    uploadId: String(d.uploadId || d.upload_id || ''),
    fileName: d.fileName || d.filename || '',
    fileSize: Number(d.fileSize ?? d.file_size_bytes ?? 0),
    detectedFormat: ((d.detectedFormat || d.detected_format || d.file_type || 'TXT').toUpperCase()) as FileFormat,
    status: d.status || 'uploaded',
    progressPercent: d.progressPercent ?? d.progress_percent ?? 0,
    message: d.message || '',
    datasetId: d.datasetId || d.dataset_id
  };
}

export const uploadService = {
  /**
   * Uploads a file to the backend staging area.
   * Throws on error — does NOT silently return fake success.
   */
  async uploadFile(file: File): Promise<DatasetUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await ApiClient.post<any>('/uploads', formData);
    if (!res.data) throw new Error('Upload failed: no response from server.');
    return normalizeUploadResponse(res.data);
  },

  /**
   * Triggers Phase 3/4 processing on a staged upload.
   * domainType must be provided by the user before calling this.
   * Throws on error.
   */
  async processUpload(
    uploadId: string,
    options?: {
      domainType?: string;
      datasetName?: string;
      columnMapping?: Record<string, string>;
    }
  ): Promise<{ datasetId: string; qualityScore: number | null; qualityStatus: string; recordsProcessed: number; message: string }> {
    if (!options?.domainType) {
      throw new Error('domainType is required to process uploaded dataset.');
    }
    const body = {
      domain_type: options.domainType,
      dataset_name: options.datasetName,
      column_mapping: options.columnMapping || {}
    };
    const res = await ApiClient.post<any>(`/uploads/${uploadId}/process`, body);
    if (!res.data) throw new Error('Processing failed: no response from server.');
    const d = res.data;
    return {
      datasetId: String(d.dataset_id || d.datasetId || ''),
      qualityScore: (d.quality_score !== undefined && d.quality_score !== null)
        ? Number(d.quality_score)
        : ((d.qualityScore !== undefined && d.qualityScore !== null) ? Number(d.qualityScore) : null),
      qualityStatus: d.quality_status || d.qualityStatus || 'pending',
      recordsProcessed: Number(d.records_processed || d.recordsProcessed || 0),
      message: d.message || 'Dataset processed and registered.'
    };
  },

  /**
   * Fetches the current upload status.
   */
  async getUploadStatus(uploadId: string): Promise<DatasetUploadResponse> {
    const res = await ApiClient.get<any>(`/uploads/${uploadId}`);
    if (!res.data) throw new Error(`Upload '${uploadId}' not found.`);
    return normalizeUploadResponse(res.data);
  },

  /**
   * Fetches a tabular preview of a staged upload (before processing).
   */
  async getUploadPreview(uploadId: string): Promise<{
    headers: string[];
    sampleRows: Record<string, string>[];
    totalPreviewRows: number;
    detectedFormat: string;
  }> {
    const res = await ApiClient.get<any>(`/uploads/${uploadId}/preview`);
    if (!res.data) throw new Error(`Preview for upload '${uploadId}' not available.`);
    const d = res.data;
    return {
      headers: Array.isArray(d.headers) ? d.headers : [],
      sampleRows: Array.isArray(d.sample_rows) ? d.sample_rows : [],
      totalPreviewRows: Number(d.total_preview_rows || 0),
      detectedFormat: (d.detected_format || 'CSV').toUpperCase()
    };
  }
};
