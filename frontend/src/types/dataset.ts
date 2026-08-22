export type DatasetDomain = 
  | 'oceanography' 
  | 'fisheries' 
  | 'biodiversity' 
  | 'molecular_edna' 
  | 'otolith' 
  | 'cross_domain';

export type DatasetStatus = 
  | 'ready' 
  | 'uploading' 
  | 'uploaded' 
  | 'processing' 
  | 'quality_checking' 
  | 'standardized'
  | 'completed' 
  | 'failed';

export type QualityStatus = 
  | 'pending'
  | 'passed'
  | 'flagged'
  | 'suspect'
  | 'failed'
  | 'excellent' 
  | 'good' 
  | 'warning' 
  | 'critical' 
  | 'unprocessed';

export type FileFormat = 'TXT' | 'CSV' | 'XLSX' | 'JSON' | 'CTD';

export interface SpatialBounds {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
  depthRange?: [number, number];
}

export interface ValidationIssue {
  id: string;
  type: 'error' | 'warning' | 'info';
  category: 'coordinates' | 'timestamp' | 'outlier' | 'schema' | 'units' | 'missing_values';
  message: string;
  affectedRowsCount: number;
  sampleRows?: number[];
  recommendation?: string;
}

export interface DatasetQualityReport {
  datasetId: string;
  score: number | null;
  status: string;
  totalRows: number;
  validRows: number;
  flaggedRows: number;
  duplicateCount: number;
  missingValueRatio: number;
  spatialCompleteness: number | null;
  temporalCompleteness: number | null;
  issues: ValidationIssue[];
  computedAt: string;
}

export interface DatasetProvenance {
  datasetId: string;
  originalFileName?: string;
  fileHashSha256: string;
  sourceInstitution?: string;
  vesselCruiseId?: string;
  dataCollector?: string;
  uploadedBy: string;
  uploadedAt: string;
  ingestionPipelineVersion?: string;
  standardizationRulesApplied: string[];
  storagePath: string;
  lineageNotes?: string;
}

export interface DatasetMetadata {
  id: string;
  title: string;
  description: string;
  domain: DatasetDomain;
  format: FileFormat;
  status: string;
  qualityStatus: string;
  qualityScore: number | null;
  rowCount: number;
  fileSizeBytes: number;
  source: string;
  region: string;
  spatialBounds?: SpatialBounds;
  temporalCoverage: {
    start: string;
    end: string;
  };
  tags: string[];
  createdAt: string;
  updatedAt: string;
  uploadedBy: string;
}

export interface DatasetUploadResponse {
  uploadId: string;
  fileName: string;
  fileSize: number;
  detectedFormat: FileFormat;
  status: DatasetStatus;
  progressPercent: number;
  message: string;
  datasetId?: string;
}

export interface DatasetPreviewData {
  datasetId: string;
  columns: {
    name: string;
    type: 'string' | 'number' | 'date' | 'boolean' | 'geo';
    unit?: string;
  }[];
  rows: Record<string, any>[];
  totalPreviewRows: number;
}
