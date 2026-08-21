import React from 'react';
import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react';
import { DatasetStatus } from '../../types/dataset';

export interface UploadProgressTrackerProps {
  currentStatus: DatasetStatus;
  progressPercent: number;
  detectedFormat?: string;
  message?: string;
}

export const UploadProgressTracker: React.FC<UploadProgressTrackerProps> = ({
  currentStatus,
  progressPercent,
  detectedFormat,
  message
}) => {
  const steps = [
    { key: 'uploading', label: 'File Ingestion', desc: 'Secure transfer to storage' },
    { key: 'processing', label: 'Format Detection & Parsing', desc: `Detected ${detectedFormat || 'TXT/CSV'}` },
    { key: 'quality_checking', label: 'Quality Control & QC Scoring', desc: 'Outlier & spatial validation' },
    { key: 'completed', label: 'Standardized & Registered', desc: 'PostGIS & WoRMS taxonomy' }
  ];

  const getStepState = (stepKey: string, index: number) => {
    const statusOrder: Record<DatasetStatus, number> = {
      ready: 0,
      uploading: 0,
      uploaded: 1,
      processing: 1,
      quality_checking: 2,
      completed: 3,
      failed: -1
    };

    const currentLevel = statusOrder[currentStatus] ?? 0;

    if (currentStatus === 'failed') {
      return 'failed';
    }
    if (currentLevel > index) {
      return 'done';
    }
    if (currentLevel === index) {
      return 'active';
    }
    return 'pending';
  };

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-6">
      {/* Progress Bar Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-white">Scientific Ingestion Pipeline</h4>
          <p className="text-xs text-slate-400 mt-0.5">{message || 'Processing dataset...'}</p>
        </div>
        <div className="text-right">
          <span className="text-sm font-mono font-bold text-ocean-cyan">{progressPercent}%</span>
        </div>
      </div>

      {/* Visual Bar */}
      <div className="w-full h-2 rounded-full bg-marine-900 overflow-hidden border border-marine-800">
        <div
          className="h-full bg-gradient-to-r from-ocean-cyan via-blue-500 to-ocean-teal transition-all duration-500 rounded-full"
          style={{ width: `${Math.max(progressPercent, 5)}%` }}
        />
      </div>

      {/* Stepper Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
        {steps.map((step, idx) => {
          const state = getStepState(step.key, idx);
          return (
            <div
              key={step.key}
              className={`p-3 rounded-xl border transition-all ${
                state === 'active'
                  ? 'bg-marine-900 border-ocean-cyan/60 shadow-glow-cyan'
                  : state === 'done'
                  ? 'bg-marine-900/60 border-ocean-teal/40'
                  : state === 'failed'
                  ? 'bg-rose-950/30 border-ocean-coral/40'
                  : 'bg-marine-950/40 border-marine-850 opacity-60'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {state === 'done' && <CheckCircle2 className="w-4 h-4 text-ocean-teal flex-shrink-0" />}
                {state === 'active' && <Loader2 className="w-4 h-4 text-ocean-cyan animate-spin flex-shrink-0" />}
                {state === 'pending' && <Circle className="w-4 h-4 text-slate-500 flex-shrink-0" />}
                {state === 'failed' && <AlertCircle className="w-4 h-4 text-ocean-coral flex-shrink-0" />}
                <span className="text-xs font-semibold text-white truncate">{step.label}</span>
              </div>
              <p className="text-[11px] text-slate-400 truncate">{step.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
