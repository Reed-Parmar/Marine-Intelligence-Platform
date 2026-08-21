import React from 'react';
import { DatasetProvenance } from '../../types/dataset';
import { ShieldCheck, GitBranch, KeyRound, HardDrive, User, Calendar, Cpu, CheckCircle2 } from 'lucide-react';

export const ProvenancePanel: React.FC<{ provenance: DatasetProvenance }> = ({ provenance }) => {
  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-ocean-cyan/10 via-marine-900 to-marine-950 border border-ocean-cyan/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-ocean-cyan/20 text-ocean-cyan">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Immutable Scientific Lineage & Audit</h4>
            <p className="text-xs text-slate-300">Verified by CMLRE Ingestion Engine with cryptographic hash stamp.</p>
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-marine-900 text-ocean-cyan border border-ocean-cyan/40">
          SHA-256 Verified
        </span>
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Source & Vessel */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-ocean-teal" />
            Origin & Sampling Lineage
          </h5>
          
          <div className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-marine-850 pb-2">
              <span className="text-slate-400">Original File:</span>
              <span className="font-mono text-white font-semibold">{provenance.originalFileName}</span>
            </div>
            <div className="flex justify-between border-b border-marine-850 pb-2">
              <span className="text-slate-400">Source Institution:</span>
              <span className="text-white text-right max-w-xs">{provenance.sourceInstitution}</span>
            </div>
            {provenance.vesselCruiseId && (
              <div className="flex justify-between border-b border-marine-850 pb-2">
                <span className="text-slate-400">Cruise / Platform:</span>
                <span className="text-ocean-cyan font-semibold">{provenance.vesselCruiseId}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-400">Data Collector:</span>
              <span className="text-white">{provenance.dataCollector || provenance.uploadedBy}</span>
            </div>
          </div>
        </div>

        {/* Cryptographic & Storage Details */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-ocean-amber" />
            Storage & Hash Security
          </h5>

          <div className="space-y-2 text-xs">
            <div>
              <span className="text-slate-400 block mb-1">SHA-256 Checksum:</span>
              <p className="p-2 rounded bg-marine-950 font-mono text-[10px] text-ocean-cyan break-all border border-marine-800">
                {provenance.fileHashSha256}
              </p>
            </div>
            <div className="flex justify-between border-b border-marine-850 pb-2">
              <span className="text-slate-400">Storage URI:</span>
              <span className="font-mono text-slate-300 truncate max-w-[200px]" title={provenance.storagePath}>
                {provenance.storagePath}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Ingestion Pipeline:</span>
              <span className="font-mono text-ocean-teal">{provenance.ingestionPipelineVersion}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Applied Standardization Rules */}
      <div className="glass-panel rounded-xl p-4 space-y-3">
        <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-ocean-cyan" />
          Standardization & Transformation Rules Applied
        </h5>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {provenance.standardizationRulesApplied.map((rule, idx) => (
            <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-marine-900/80 border border-marine-800 text-xs text-slate-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-ocean-teal flex-shrink-0" />
              <span>{rule}</span>
            </div>
          ))}
        </div>

        {provenance.lineageNotes && (
          <div className="pt-2 border-t border-marine-800 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Calibration Notes: </span>
            {provenance.lineageNotes}
          </div>
        )}
      </div>
    </div>
  );
};
