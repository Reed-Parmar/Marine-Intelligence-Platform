import React from 'react';
import { AnalysisResultData } from '../../types/analysis';
import { GitCommit, Database, Cpu, Clock } from 'lucide-react';

export const ProvenanceTrace: React.FC<{ provenance: AnalysisResultData['provenance'] }> = ({
  provenance
}) => {
  return (
    <div className="glass-panel rounded-xl p-4 space-y-3 bg-marine-950/60 border border-marine-800">
      <div className="flex items-center justify-between border-b border-marine-850 pb-2">
        <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <GitCommit className="w-4 h-4 text-ocean-cyan" />
          Computation Provenance & Input Lineage
        </span>
        <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
          <Clock className="w-3 h-3 text-slate-400" />
          {new Date(provenance.computedTimestamp).toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-slate-400 block mb-1">Source Datasets Fused:</span>
          <div className="flex flex-wrap gap-1.5">
            {provenance.inputDatasetIds.map((id) => (
              <span key={id} className="font-mono text-[11px] px-2 py-0.5 rounded bg-marine-900 border border-marine-700 text-ocean-cyan">
                {id}
              </span>
            ))}
          </div>
        </div>

        <div>
          <span className="text-slate-400 block mb-1">Algorithm Execution:</span>
          <p className="font-mono text-[11px] text-slate-200">
            {provenance.algorithmName} ({provenance.recordsUsedCount.toLocaleString()} records ingested)
          </p>
        </div>
      </div>
    </div>
  );
};
