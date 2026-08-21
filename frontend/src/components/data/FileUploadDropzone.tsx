import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, FileSpreadsheet, FileCode } from 'lucide-react';
import { Button } from '../ui/Button';

export interface FileUploadDropzoneProps {
  onFileSelected: (file: File) => void;
  isLoading?: boolean;
}

export const FileUploadDropzone: React.FC<FileUploadDropzoneProps> = ({
  onFileSelected,
  isLoading = false
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const supportedFormats = ['.txt', '.csv', '.xlsx', '.json', '.ctd'];

  const validateAndSelect = (file: File) => {
    setErrorMsg(null);
    const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');
    if (!supportedFormats.includes(ext)) {
      setErrorMsg(`Unsupported file type (${ext}). Please provide a CMLRE standard TXT, CSV, CTD, XLSX, or JSON.`);
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      setErrorMsg('File size exceeds 100 MB limit.');
      return;
    }
    setSelectedFile(file);
    onFileSelected(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const selectMockFile = (name: string, format: string) => {
    const mockContent = 'sample_id\tscientific_name\tdecimal_latitude\tdecimal_longitude\tsampling_depth\nCMLRE-01\tRastrelliger kanagurta\t9.94\t75.82\t25';
    const blob = new Blob([mockContent], { type: 'text/plain' });
    const file = new File([blob], name, { type: 'text/plain' });
    validateAndSelect(file);
  };

  return (
    <div className="space-y-4">
      {/* Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`glass-panel rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 border-2 border-dashed ${
          dragActive
            ? 'border-ocean-cyan bg-marine-900/90 shadow-glow-cyan'
            : selectedFile
            ? 'border-ocean-teal/60 bg-marine-900/70'
            : 'border-marine-700 hover:border-ocean-cyan/50 hover:bg-marine-900/60'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.csv,.xlsx,.json,.ctd"
          onChange={handleChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-marine-900 border border-marine-800 flex items-center justify-center mb-4 text-ocean-cyan shadow-inner">
            {selectedFile ? (
              <CheckCircle2 className="w-8 h-8 text-ocean-teal animate-fade-in" />
            ) : (
              <UploadCloud className="w-8 h-8 text-ocean-cyan" />
            )}
          </div>

          <h4 className="text-base font-semibold text-white">
            {selectedFile ? selectedFile.name : 'Select or drag & drop marine dataset'}
          </h4>
          
          <p className="text-xs text-slate-400 mt-1 max-w-sm">
            {selectedFile
              ? `${(selectedFile.size / 1024).toFixed(1)} KB — Click to change file`
              : 'Supports CMLRE TXT files, CTD casts, Darwin Core CSVs, Excel, and JSON'}
          </p>

          {/* Supported Format Pills */}
          <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
            <span className="px-2 py-0.5 rounded bg-marine-950 border border-ocean-cyan/40 text-ocean-cyan text-[10px] font-mono font-bold">
              TXT (CMLRE)
            </span>
            <span className="px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 text-[10px] font-mono">
              CSV
            </span>
            <span className="px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 text-[10px] font-mono">
              CTD
            </span>
            <span className="px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 text-[10px] font-mono">
              XLSX
            </span>
            <span className="px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 text-[10px] font-mono">
              JSON
            </span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-950/40 border border-ocean-coral/40 text-ocean-coral text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Quick CMLRE Preset Demo Files */}
      <div className="glass-panel rounded-xl p-4">
        <p className="text-xs font-semibold text-slate-300 mb-2.5">
          Quick Demo: Ingest standard CMLRE expedition files
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => selectMockFile('dnaderiveddata1.txt', 'TXT')}
            className="flex items-center gap-2 p-2.5 rounded-lg bg-marine-900/80 hover:bg-marine-800 border border-marine-800 hover:border-ocean-cyan/50 text-left transition-all group"
          >
            <FileCode className="w-4 h-4 text-ocean-cyan flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate group-hover:text-ocean-cyan">dnaderiveddata1.txt</p>
              <p className="text-[10px] text-slate-400">eDNA Molecular File</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => selectMockFile('occurrence.txt', 'TXT')}
            className="flex items-center gap-2 p-2.5 rounded-lg bg-marine-900/80 hover:bg-marine-800 border border-marine-800 hover:border-ocean-teal/50 text-left transition-all group"
          >
            <FileText className="w-4 h-4 text-ocean-teal flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate group-hover:text-ocean-teal">occurrence.txt</p>
              <p className="text-[10px] text-slate-400">Species Darwin Core</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => selectMockFile('ctd_arabian_sea_monsoon.ctd', 'CTD')}
            className="flex items-center gap-2 p-2.5 rounded-lg bg-marine-900/80 hover:bg-marine-800 border border-marine-800 hover:border-ocean-amber/50 text-left transition-all group"
          >
            <FileSpreadsheet className="w-4 h-4 text-ocean-amber flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate group-hover:text-ocean-amber">arabian_sea_cast.ctd</p>
              <p className="text-[10px] text-slate-400">CTD Hydrography</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
