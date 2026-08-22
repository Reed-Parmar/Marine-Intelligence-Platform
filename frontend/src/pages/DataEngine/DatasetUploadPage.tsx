import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadService } from '../../services/uploads';
import { DatasetStatus } from '../../types/dataset';
import { useToast } from '../../context/ToastContext';
import { FileUploadDropzone } from '../../components/data/FileUploadDropzone';
import { UploadProgressTracker } from '../../components/data/UploadProgressTracker';
import { QualityScoreBadge } from '../../components/data/QualityScoreBadge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import {
  CheckCircle2, ArrowRight, FileText, AlertTriangle
} from 'lucide-react';

const DOMAIN_OPTIONS = [
  { value: 'oceanography', label: 'Oceanography / CTD Hydrography' },
  { value: 'fisheries', label: 'Commercial Fisheries' },
  { value: 'biodiversity', label: 'Species & Biodiversity (Darwin Core)' },
  { value: 'molecular_edna', label: 'Molecular eDNA / Metabarcoding' },
];

interface ProcessResult {
  datasetId: string;
  qualityScore: number | null;
  qualityStatus: string;
  recordsProcessed: number;
  message: string;
}

export const DatasetUploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [domainType, setDomainType] = useState<string>('oceanography');
  const [uploadStatus, setUploadStatus] = useState<DatasetStatus>('ready');
  const [progress, setProgress] = useState<number>(0);
  const [detectedFormat, setDetectedFormat] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [processResult, setProcessResult] = useState<ProcessResult | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    headers: string[];
    sampleRows: Record<string, string>[];
  } | null>(null);

  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleFileSelected = async (selectedFile: File, suggestedDomain?: string) => {
    const activeDomain = suggestedDomain || domainType;
    if (suggestedDomain) {
      setDomainType(suggestedDomain);
    }
    setFile(selectedFile);
    setUploadStatus('uploading');
    setProgress(15);
    setStatusMessage(`Uploading ${selectedFile.name} to CMLRE staging area...`);
    setProcessResult(null);
    setPreview(null);

    try {
      // Step 1: Upload to staging
      const uploadRes = await uploadService.uploadFile(selectedFile);
      setUploadId(uploadRes.uploadId);
      setDetectedFormat(uploadRes.detectedFormat);
      setProgress(40);
      setUploadStatus('processing');
      setStatusMessage(`Format detected: ${uploadRes.detectedFormat}. Fetching preview...`);

      // Step 2: Fetch preview while user sees progress
      try {
        const previewData = await uploadService.getUploadPreview(uploadRes.uploadId);
        setPreview({ headers: previewData.headers, sampleRows: previewData.sampleRows });
      } catch {
        // Preview is optional — processing can still succeed
      }

      setProgress(70);
      setUploadStatus('quality_checking');
      setStatusMessage(`Standardizing ${selectedFile.name} & running Phase 4 Quality Control...`);

      // Step 3: Process the upload (triggers Phase 3/4 pipeline)
      const result = await uploadService.processUpload(uploadRes.uploadId, {
        domainType: activeDomain,
        datasetName: selectedFile.name.replace(/\.[^/.]+$/, '')
      });

      setProcessResult(result);
      setProgress(100);
      setUploadStatus('completed');
      setStatusMessage(result.message || 'Dataset successfully processed and registered.');
      addToast('success', 'Dataset Ingestion Complete', `${selectedFile.name} is now queryable in the Data Engine.`);

    } catch (err: any) {
      setUploadStatus('failed');
      setStatusMessage(err.message || 'Ingestion failed. Check backend connection and file format.');
      addToast('error', 'Ingestion Failed', err.message || 'Unknown error during upload or processing.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadStatus('ready');
    setProgress(0);
    setProcessResult(null);
    setUploadId(null);
    setPreview(null);
    setStatusMessage('');
  };

  const qualityBadgeStatus = (qs: string | null): 'excellent' | 'good' | 'fair' | 'poor' | 'pending' => {
    if (!qs) return 'pending';
    if (qs === 'excellent') return 'excellent';
    if (qs === 'good') return 'good';
    if (qs === 'fair') return 'fair';
    if (qs === 'poor') return 'poor';
    return 'pending';
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {uploadStatus === 'ready' ? (
        <div className="space-y-4">
          {/* Domain Type Selector */}
          <div className="p-4 rounded-2xl bg-marine-900/60 border border-marine-800 space-y-3">
            <div className="text-xs font-semibold text-slate-200">
              Step 1: Select Scientific Domain
            </div>
            <select
              value={domainType}
              onChange={(e) => setDomainType(e.target.value)}
              className="w-full bg-marine-950 border border-marine-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan"
            >
              {DOMAIN_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <div className="text-[11px] text-slate-400">
              <span className="font-semibold text-white">Accepted formats: </span>
              Comma/tab-delimited TXT, CSV, CTD hydrography profiles (with preamble comments), Darwin Core occurrence CSV, and eDNA metadata XLSX.
            </div>
          </div>

          <div className="text-xs font-semibold text-slate-200 px-1">Step 2: Upload File</div>
          <FileUploadDropzone onFileSelected={handleFileSelected} />
        </div>
      ) : (
        <div className="space-y-6">
          <UploadProgressTracker
            currentStatus={uploadStatus}
            progressPercent={progress}
            detectedFormat={detectedFormat}
            message={statusMessage}
          />

          {/* Preview table — shows real uploaded content before processing completes */}
          {preview && preview.headers.length > 0 && (
            <Card className="border-marine-800/60 bg-marine-900/60 space-y-3">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                <FileText className="w-4 h-4 text-ocean-cyan" />
                File Preview (first {preview.sampleRows.length} rows from <span className="font-mono text-ocean-cyan">{file?.name}</span>)
              </div>
              <div className="overflow-x-auto rounded-lg border border-marine-800">
                <table className="w-full text-xs font-mono">
                  <thead className="bg-marine-950">
                    <tr>
                      {preview.headers.map(h => (
                        <th key={h} className="px-3 py-2 text-left text-slate-400 whitespace-nowrap border-b border-marine-800">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.sampleRows.map((row, i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-marine-900' : 'bg-marine-950'}>
                        {preview.headers.map(h => (
                          <td key={h} className="px-3 py-1.5 text-slate-300 whitespace-nowrap border-b border-marine-800/50">
                            {row[h] ?? '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {uploadStatus === 'completed' && processResult && (
            <Card className="border-ocean-teal/40 bg-marine-900/80 space-y-4 animate-slide-up">
              <div className="flex items-center justify-between border-b border-marine-800 pb-3">
                <div className="flex items-center gap-2 text-ocean-teal font-semibold text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Dataset Ingested & Registered</span>
                </div>
                {processResult.qualityScore !== null ? (
                  <QualityScoreBadge
                    score={Math.round(processResult.qualityScore)}
                    status={qualityBadgeStatus(processResult.qualityStatus)}
                  />
                ) : (
                  <span className="text-xs text-slate-400 font-mono">QC: Pending</span>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-marine-950 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">File Name:</span>
                  <span className="text-white truncate block">{file?.name}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-marine-950 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">Detected Format:</span>
                  <span className="text-ocean-cyan font-bold">{detectedFormat}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-marine-950 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">Records Processed:</span>
                  <span className="text-emerald-400 font-bold">
                    {processResult.recordsProcessed.toLocaleString()}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-marine-950 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">Domain:</span>
                  <span className="text-ocean-teal font-bold">
                    {DOMAIN_OPTIONS.find(d => d.value === domainType)?.label.split(' ')[0] || domainType}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <Button size="sm" variant="ghost" onClick={handleReset}>
                  Ingest Another File
                </Button>
                <Button
                  size="md"
                  variant="primary"
                  onClick={() => navigate(`/data/datasets/${processResult.datasetId}`)}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                  disabled={!processResult.datasetId}
                >
                  Inspect Dataset & Preview
                </Button>
              </div>
            </Card>
          )}

          {uploadStatus === 'failed' && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-ocean-coral/40 flex items-center justify-between">
              <div className="flex items-center gap-2 text-ocean-coral text-xs">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{statusMessage}</span>
              </div>
              <Button size="sm" variant="outline" onClick={handleReset}>
                Try Again
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
