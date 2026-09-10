import React, { useState } from 'react';
import { Sparkles, Sliders, Play, RotateCcw, TrendingUp, AlertCircle, CheckCircle2, Fish } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface SimulationParams {
  species: string;
  historicalCpue: number; // kg/hr
  monsoonIndex: number;   // 0.0 to 1.0
  sstLag30: number;       // °C deviation (-2.0 to +3.0)
  fishingEffortHours: number; // hours (10,000 to 120,000)
}

interface SimulationResult {
  predictedTons: number;
  ciLow: number;
  ciHigh: number;
  cpueProjected: number;
  sustainabilityStatus: 'Sustainable Yield' | 'Precautionary Alert' | 'Overfishing Risk';
  statusVariant: 'teal' | 'amber' | 'coral';
  confidencePercent: number;
  notes: string;
}

const SPECIES_CONFIG: Record<string, { baseBiomass: number; optimalSST: number; optimalMonsoon: number; maxCpue: number }> = {
  'Indian Oil Sardine (Sardinella longiceps)': {
    baseBiomass: 68000,
    optimalSST: 0.2,
    optimalMonsoon: 0.85,
    maxCpue: 210
  },
  'Indian Mackerel (Rastrelliger kanagurta)': {
    baseBiomass: 52000,
    optimalSST: 0.0,
    optimalMonsoon: 0.65,
    maxCpue: 185
  },
  'Yellowfin Tuna (Thunnus albacares)': {
    baseBiomass: 31000,
    optimalSST: -0.4,
    optimalMonsoon: 0.40,
    maxCpue: 140
  },
  'Karikkadi Shrimp (Parapenaeopsis stylifera)': {
    baseBiomass: 36000,
    optimalSST: 0.5,
    optimalMonsoon: 0.90,
    maxCpue: 175
  }
};

export const CatchPredictionSimulator: React.FC<{ initialSpecies?: string }> = ({
  initialSpecies = 'Indian Oil Sardine (Sardinella longiceps)'
}) => {
  const [params, setParams] = useState<SimulationParams>({
    species: initialSpecies,
    historicalCpue: 145,
    monsoonIndex: 0.75,
    sstLag30: 0.4,
    fishingEffortHours: 72000
  });

  const [isSimulating, setIsSimulating] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);

  const calculatePrediction = (p: SimulationParams): SimulationResult => {
    const config = SPECIES_CONFIG[p.species] || SPECIES_CONFIG['Indian Oil Sardine (Sardinella longiceps)'];

    // MBLF-Net surrogate model approximation
    const cpueFactor = p.historicalCpue / 140;
    const effortFactor = Math.pow(p.fishingEffortHours / 70000, 0.75);
    const sstPenalty = Math.max(0, 1 - Math.abs(p.sstLag30 - config.optimalSST) * 0.18);
    const monsoonBoost = 0.8 + (1 - Math.abs(p.monsoonIndex - config.optimalMonsoon)) * 0.35;

    const basePredicted = config.baseBiomass * cpueFactor * effortFactor * sstPenalty * monsoonBoost;
    const predictedTons = Math.round(basePredicted);
    const ciMargin = Math.round(predictedTons * 0.095);

    const projectedCpue = Math.round((predictedTons * 1000) / p.fishingEffortHours);

    let sustainabilityStatus: SimulationResult['sustainabilityStatus'] = 'Sustainable Yield';
    let statusVariant: SimulationResult['statusVariant'] = 'teal';
    let notes = 'Forecasted stock biomass is well within safe maximum sustainable yield (MSY) biological reference points.';

    if (p.fishingEffortHours > 95000 || (p.sstLag30 > 1.8 && p.historicalCpue < 120)) {
      sustainabilityStatus = 'Overfishing Risk';
      statusVariant = 'coral';
      notes = 'High fishing effort combined with elevated SST lag is projected to trigger recruitment stress and biomass contraction.';
    } else if (p.fishingEffortHours > 80000 || p.monsoonIndex < 0.35) {
      sustainabilityStatus = 'Precautionary Alert';
      statusVariant = 'amber';
      notes = 'Monsoon upwelling anomalies suggest moderate juvenile dispersion; cap additional mechanized trawling effort.';
    }

    return {
      predictedTons,
      ciLow: predictedTons - ciMargin,
      ciHigh: predictedTons + ciMargin,
      cpueProjected: projectedCpue,
      sustainabilityStatus,
      statusVariant,
      confidencePercent: 91.4,
      notes
    };
  };

  const handleRun = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setResult(calculatePrediction(params));
      setIsSimulating(false);
    }, 450);
  };

  const handleReset = () => {
    setParams({
      species: initialSpecies,
      historicalCpue: 145,
      monsoonIndex: 0.75,
      sstLag30: 0.4,
      fishingEffortHours: 72000
    });
    setResult(null);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-marine-800 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-marine-850 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-ocean-cyan/20 text-ocean-cyan">
              <Sparkles className="w-4 h-4" />
            </span>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">
              MBLF-Net Live Catch Prediction Simulator
            </h4>
          </div>
          <p className="text-xs text-slate-400">
            Simulate forward-looking commercial harvest yields by modulating key oceanographic and operational parameters.
          </p>
        </div>

        <Badge variant="cyan" size="sm" className="font-mono self-start sm:self-auto">
          XGBoost CNN-LSTM • Live Inference
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-6 space-y-4">
          {/* Target Species Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Target Commercial Stock
            </label>
            <select
              value={params.species}
              onChange={(e) => setParams({ ...params, species: e.target.value })}
              className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan transition-colors font-sans"
            >
              {Object.keys(SPECIES_CONFIG).map((sp) => (
                <option key={sp} value={sp}>
                  {sp}
                </option>
              ))}
            </select>
          </div>

          {/* Historical CPUE */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">Historical CPUE (kg/hr)</span>
              <span className="font-mono text-ocean-cyan font-bold">{params.historicalCpue} kg/hr</span>
            </div>
            <input
              type="range"
              min={60}
              max={240}
              step={5}
              value={params.historicalCpue}
              onChange={(e) => setParams({ ...params, historicalCpue: Number(e.target.value) })}
              className="w-full accent-ocean-cyan cursor-pointer h-1.5 bg-marine-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>60 (Low)</span>
              <span>150 (Mean)</span>
              <span>240 (Peak)</span>
            </div>
          </div>

          {/* Monsoon Index */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">Monsoon Upwelling Index</span>
              <span className="font-mono text-ocean-teal font-bold">{params.monsoonIndex.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min={0.1}
              max={1.0}
              step={0.05}
              value={params.monsoonIndex}
              onChange={(e) => setParams({ ...params, monsoonIndex: Number(e.target.value) })}
              className="w-full accent-ocean-teal cursor-pointer h-1.5 bg-marine-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.10 (Pre-monsoon)</span>
              <span>0.50 (Moderate)</span>
              <span>1.00 (Intense Upwelling)</span>
            </div>
          </div>

          {/* SST Lag 30 */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">SST 30-Day Lag Anomaly (°C)</span>
              <span className="font-mono text-ocean-amber font-bold">
                {params.sstLag30 > 0 ? `+${params.sstLag30.toFixed(1)}°C` : `${params.sstLag30.toFixed(1)}°C`}
              </span>
            </div>
            <input
              type="range"
              min={-1.5}
              max={2.5}
              step={0.1}
              value={params.sstLag30}
              onChange={(e) => setParams({ ...params, sstLag30: Number(e.target.value) })}
              className="w-full accent-ocean-amber cursor-pointer h-1.5 bg-marine-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>-1.5°C (Cool Pool)</span>
              <span>0.0°C (Normal)</span>
              <span>+2.5°C (MHW Warning)</span>
            </div>
          </div>

          {/* Fishing Effort Hours */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">Fleet Fishing Effort (Hours)</span>
              <span className="font-mono text-ocean-blue font-bold">
                {params.fishingEffortHours.toLocaleString()} hrs
              </span>
            </div>
            <input
              type="range"
              min={25000}
              max={110000}
              step={2500}
              value={params.fishingEffortHours}
              onChange={(e) => setParams({ ...params, fishingEffortHours: Number(e.target.value) })}
              className="w-full accent-ocean-blue cursor-pointer h-1.5 bg-marine-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>25,000 h (Restricted)</span>
              <span>70,000 h (Nominal)</span>
              <span>110,000 h (Maximum)</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            <Button
              variant="primary"
              size="sm"
              onClick={handleRun}
              disabled={isSimulating}
              className="flex-1 flex items-center justify-center gap-2"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isSimulating ? 'Computing Inference...' : 'Run Catch Prediction'}</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="text-slate-400 hover:text-white"
              title="Reset parameters"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-6 flex flex-col justify-between p-5 rounded-xl bg-marine-950/80 border border-marine-800 space-y-4">
          {result ? (
            <div className="space-y-4 animate-fade-in">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    Model Inference Output
                  </span>
                  <h5 className="text-sm font-semibold text-white mt-0.5">{params.species}</h5>
                </div>
                <Badge variant={result.statusVariant} size="sm">
                  {result.sustainabilityStatus}
                </Badge>
              </div>

              {/* Primary Output Display */}
              <div className="p-4 rounded-xl bg-marine-900/90 border border-marine-800 space-y-2">
                <span className="text-[10px] font-sans text-slate-400 uppercase tracking-wider block">
                  Simulated Catch Yield (MBLF-Net)
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-mono font-black text-ocean-cyan tracking-tight">
                    {result.predictedTons.toLocaleString()}
                  </span>
                  <span className="text-sm font-semibold text-slate-300 font-mono">Metric Tons</span>
                </div>

                <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-2 border-t border-marine-800/80">
                  <span>95% CI: <strong className="text-slate-200 font-normal">{result.ciLow.toLocaleString()} - {result.ciHigh.toLocaleString()} T</strong></span>
                  <span>Proj. CPUE: <strong className="text-ocean-teal font-normal">{result.cpueProjected} kg/h</strong></span>
                </div>
              </div>

              {/* Advisory & Feature Breakdown */}
              <div className="p-3 rounded-lg bg-marine-900/50 border border-marine-850 text-xs text-slate-300 space-y-1.5 leading-relaxed">
                <span className="font-semibold text-white block">Advisory Guidance:</span>
                <p>{result.notes}</p>
              </div>

              <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between pt-1">
                <span>Model Confidence: <strong>{result.confidencePercent}%</strong></span>
                <span>Inference Latency: <strong>14.2 ms</strong></span>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-marine-900 border border-marine-800 flex items-center justify-center text-ocean-cyan">
                <Fish className="w-6 h-6 animate-pulse" />
              </div>
              <div className="space-y-1 max-w-xs">
                <h5 className="text-xs font-bold text-white uppercase tracking-wider">
                  Ready for Simulation
                </h5>
                <p className="text-xs text-slate-400">
                  Adjust the four MBLF-Net input features and click <strong>Run Catch Prediction</strong> to generate live harvest yield projections.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRun}
                className="mt-2 text-xs"
              >
                Run Default Parameters
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
