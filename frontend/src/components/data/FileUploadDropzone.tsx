import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, FileSpreadsheet, FileCode } from 'lucide-react';
import { Button } from '../ui/Button';

export interface FileUploadDropzoneProps {
  onFileSelected: (file: File, suggestedDomain?: string) => void;
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

  const inferDomainFromFilename = (filename: string): string | undefined => {
    const lower = filename.toLowerCase();
    if (lower.includes('dna') || lower.includes('edna') || lower.includes('meta')) return 'molecular_edna';
    if (lower.includes('occur') || lower.includes('species') || lower.includes('biodiv') || lower.includes('taxa')) return 'biodiversity';
    if (lower.includes('ctd') || lower.includes('ocean') || lower.includes('hydro') || lower.includes('temp') || lower.includes('salinity')) return 'oceanography';
    if (lower.includes('fish') || lower.includes('catch') || lower.includes('trawl') || lower.includes('landing')) return 'fisheries';
    return undefined;
  };

  const validateAndSelect = (file: File, explicitDomain?: string) => {
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
    const suggestedDomain = explicitDomain || inferDomainFromFilename(file.name);
    setSelectedFile(file);
    onFileSelected(file, suggestedDomain);
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

  const selectMockFile = (name: string, domain: string) => {
    let mockContent = '';
    if (domain === 'molecular_edna') {
      mockContent = 'sample_code\tlatitude\tlongitude\tdepth_meters\ttarget_gene\tsequencing_platform\tassigned_scientific_name\tread_count\tblast_identity_percentage\nEDNA-AS-01\t10.85\t72.25\t25.0\t16S rRNA / COI\tIllumina NovaSeq 6000\tSynechococcus sp.\t1420\t99.4\nEDNA-AS-02\t10.85\t72.25\t50.0\t16S rRNA / COI\tIllumina NovaSeq 6000\tPelagibacter ubique\t3850\t98.9\nEDNA-AS-03\t11.25\t73.10\t15.0\t16S rRNA / COI\tIllumina NovaSeq 6000\tProchlorococcus marinus\t2100\t99.8';
    } else if (domain === 'biodiversity') {
      mockContent = 'id\tscientificName\tdecimalLatitude\tdecimalLongitude\tminimumDepthInMeters\tindividualCount\teventDate\tbasisOfRecord\toccurrenceStatus\n93630\tAsterionella japonica\t16.2551\t69.9113\t25\t1\t2009-02-16\tHumanObservation\tpresent\n93631\tBacteriastrum hyalinum\t16.2551\t69.9113\t25\t1\t2009-02-16\tHumanObservation\tpresent\n93632\tChaetoceros concavicornis\t16.2551\t69.9113\t25\t1\t2009-02-16\tHumanObservation\tpresent';
    } else {
      mockContent = 'station_id\tlatitude\tlongitude\tdepth_meters\ttemperature_celsius\tsalinity_psu\tdissolved_oxygen_mgl\tchlorophyll_mg_m3\tph\ttimestamp\nCMLRE-CTD-01\t15.42\t72.18\t10.0\t28.45\t35.21\t5.82\t1.45\t8.14\t2023-08-15T06:00:00Z\nCMLRE-CTD-01\t15.42\t72.18\t50.0\t26.12\t35.88\t4.15\t0.82\t8.05\t2023-08-15T06:15:00Z\nCMLRE-CTD-01\t15.42\t72.18\t100.0\t21.30\t36.14\t2.30\t0.18\t7.92\t2023-08-15T06:30:00Z';
    }
    const blob = new Blob([mockContent], { type: 'text/plain' });
    const file = new File([blob], name, { type: 'text/plain' });
    validateAndSelect(file, domain);
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
            onClick={() => selectMockFile('dnaderiveddata1.txt', 'molecular_edna')}
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
            onClick={() => selectMockFile('occurrence.txt', 'biodiversity')}
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
            onClick={() => selectMockFile('ctd_arabian_sea_monsoon.ctd', 'oceanography')}
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
