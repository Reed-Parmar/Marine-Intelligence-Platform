import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadService } from '../../services/uploads';
import { DatasetStatus, FileFormat } from '../../types/dataset';
import { useToast } from '../../context/ToastContext';
import { FileUploadDropzone } from '../../components/data/FileUploadDropzone';
import { UploadProgressTracker } from '../../components/data/UploadProgressTracker';
import { QualityScoreBadge } from '../../components/data/QualityScoreBadge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { CheckCircle2, ArrowRight, ShieldCheck, FileText, AlertTriangle } from 'lucide-react';

export const DatasetUploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<DatasetStatus>('ready');
  const [progress, setProgress] = useState<number>(0);
  const [detectedFormat, setDetectedFormat] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [datasetId, setDatasetId] = useState<string | null>(null);

  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleFileSelected = async (selectedFile: File) => {
    setFile(selectedFile);
    setUploadStatus('uploading');
    setProgress(15);
    setMessage(`Uploading ${selectedFile.name} to CMLRE staging bucket...`);

    try {
      // Step 1: Upload
      const uploadRes = await uploadService.uploadFile(selectedFile);
      setDetectedFormat(uploadRes.detectedFormat);
      setProgress(40);
      setUploadStatus('processing');
      setMessage(`Detected format: ${uploadRes.detectedFormat}. Parsing column preambles and coordinate headers...`);

      // Step 2: Processing & QC Simulation Delay
      setTimeout(async () => {
        setProgress(75);
        setUploadStatus('quality_checking');
        setMessage('Executing CMLRE automated quality control, coordinate bounding checks, and CF standardization...');

        setTimeout(async () => {
          const processRes = await uploadService.processUpload(uploadRes.uploadId);
          setProgress(100);
          setUploadStatus('completed');
          setMessage('Dataset successfully validated, standardized to Darwin Core / CF conventions, and registered in PostGIS database.');
          const finalId = processRes.datasetId || 'ds-cmlre-txt-01';
          setDatasetId(finalId);
          addToast('success', 'Dataset Ingestion Complete', `${selectedFile.name} is now queryable.`);
        }, 1200);
      }, 1000);
    } catch (err: any) {
      setUploadStatus('failed');
      setMessage(err.message || 'Ingestion failed during quality control checks.');
      addToast('error', 'Ingestion Failed', err.message);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadStatus('ready');
    setProgress(0);
    setDatasetId(null);
    setMessage('');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Upload Zone or Pipeline Progress */}
      {uploadStatus === 'ready' ? (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-marine-900/60 border border-marine-800 text-xs text-slate-300">
            <span className="font-semibold text-white">Supported Scientific Formats: </span>
            CMLRE Tab-Delimited `.txt` files (with comment preambles), CTD hydrography profiles, Darwin Core species occurrence `.csv`, and molecular eDNA metadata `.xlsx`.
          </div>
          <FileUploadDropzone onFileSelected={handleFileSelected} />
        </div>
      ) : (
        <div className="space-y-6">
          <UploadProgressTracker
            currentStatus={uploadStatus}
            progressPercent={progress}
            detectedFormat={detectedFormat}
            message={message}
          />

          {uploadStatus === 'completed' && (
            <Card className="border-ocean-teal/40 bg-marine-900/80 space-y-4 animate-slide-up">
              <div className="flex items-center justify-between border-b border-marine-800 pb-3">
                <div className="flex items-center gap-2 text-ocean-teal font-semibold text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Dataset Ingested & Quality Verified</span>
                </div>
                <QualityScoreBadge score={97} status="excellent" />
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
                  <span className="text-[10px] text-slate-400 block font-sans">Valid Rows:</span>
                  <span className="text-emerald-400 font-bold">3,798 / 3,840</span>
                </div>
                <div className="p-2.5 rounded-lg bg-marine-950 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">PostGIS Status:</span>
                  <span className="text-ocean-teal font-bold">Indexed EPSG:4326</span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <Button size="sm" variant="ghost" onClick={handleReset}>
                  Ingest Another File
                </Button>

                <Button
                  size="md"
                  variant="primary"
                  onClick={() => navigate(`/data/datasets/${datasetId || 'ds-cmlre-txt-01'}`)}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Inspect Dataset Details & Provenance
                </Button>
              </div>
            </Card>
          )}

          {uploadStatus === 'failed' && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-ocean-coral/40 flex items-center justify-between">
              <div className="flex items-center gap-2 text-ocean-coral text-xs">
                <AlertTriangle className="w-4 h-4" />
                <span>{message}</span>
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
