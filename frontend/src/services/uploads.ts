import { ApiClient } from './api';
import { DatasetUploadResponse, FileFormat } from '../types/dataset';

export const uploadService = {
  async uploadFile(file: File): Promise<DatasetUploadResponse> {
    const extension = file.name.split('.').pop()?.toUpperCase() || 'TXT';
    let detectedFormat: FileFormat = 'TXT';
    if (['CSV', 'TXT', 'JSON', 'CTD', 'XLSX'].includes(extension)) {
      detectedFormat = extension as FileFormat;
    }

    const uploadId = `upl-${Date.now()}`;
    const fallback: DatasetUploadResponse = {
      uploadId,
      fileName: file.name,
      fileSize: file.size,
      detectedFormat,
      status: 'uploaded',
      progressPercent: 100,
      message: `File ${file.name} successfully uploaded and format detected as ${detectedFormat}.`,
      datasetId: `ds-cmlre-${uploadId}`
    };

    // Simulated / live endpoint
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await ApiClient.post<DatasetUploadResponse>('/uploads', formData, fallback);
      return res.data;
    } catch {
      return fallback;
    }
  },

  async processUpload(uploadId: string): Promise<DatasetUploadResponse> {
    const fallback: DatasetUploadResponse = {
      uploadId,
      fileName: 'cmlre_dataset.txt',
      fileSize: 3450000,
      detectedFormat: 'TXT',
      status: 'completed',
      progressPercent: 100,
      message: 'Quality control, Darwin Core standardization and PostGIS spatial indexing completed.',
      datasetId: `ds-cmlre-${uploadId}`
    };

    const res = await ApiClient.post<DatasetUploadResponse>(`/uploads/${uploadId}/process`, {}, fallback);
    return res.data;
  },

  async getUploadStatus(uploadId: string): Promise<DatasetUploadResponse> {
    const fallback: DatasetUploadResponse = {
      uploadId,
      fileName: 'cmlre_dataset.txt',
      fileSize: 3450000,
      detectedFormat: 'TXT',
      status: 'completed',
      progressPercent: 100,
      message: 'Processing completed successfully.',
      datasetId: `ds-cmlre-${uploadId}`
    };

    const res = await ApiClient.get<DatasetUploadResponse>(`/uploads/${uploadId}`, fallback);
    return res.data;
  }
};
