import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-500/30 flex items-start gap-3 text-xs text-blue-200">
      <ShieldAlert className="w-5 h-5 text-ocean-cyan flex-shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold text-white">Scientific Decision-Support Advisory</p>
        <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">
          AI/ML models (Isolation Forest, MaxEnt Ecological Niche, LSTM-XGBoost) provide predictive decision support based on ingested CMLRE observations. Outputs are probabilistic recommendations and must be evaluated alongside ground-truth cruise measurements.
        </p>
      </div>
    </div>
  );
};
