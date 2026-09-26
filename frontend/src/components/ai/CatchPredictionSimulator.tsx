import React, { useState } from 'react';
import { Sparkles, Play, RotateCcw, TrendingUp, AlertCircle, CheckCircle2, Fish, Ship, Compass, Calendar, Anchor } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { fisheriesService } from '../../services/fisheries';
import { FisheriesCatchPredictionParams, FisheriesCatchPredictionResult } from '../../types/fisheries';

const FLEET_OPTIONS = [
  { value: 'EUESP', label: 'EUESP — European Union (Spain)' },
  { value: 'EUFRA', label: 'EUFRA — European Union (France)' },
  { value: 'SYC', label: 'SYC — Seychelles' },
  { value: 'MDV', label: 'MDV — Maldives' },
  { value: 'JPN', label: 'JPN — Japan' },
  { value: 'IND', label: 'IND — India' },
  { value: 'IDN', label: 'IDN — Indonesia' },
  { value: 'LKA', label: 'LKA — Sri Lanka' },
];

const GEAR_OPTIONS = [
  { value: 'PS', label: 'PS — Purse Seine' },
  { value: 'BB', label: 'BB — Baitboat / Pole and Line' },
  { value: 'LL', label: 'LL — Longline' },
  { value: 'RIN', label: 'RIN — Ring Net' },
];

const EFFORT_UNIT_OPTIONS = [
  { value: 'FHOURS', label: 'FHOURS — Fishing Hours' },
  { value: 'FDAYS', label: 'FDAYS — Fishing Days' },
  { value: 'SETS', label: 'SETS — Number of Sets' },
  { value: 'TRIPS', label: 'TRIPS — Fishing Trips' },
];

export const CatchPredictionSimulator: React.FC<{ initialSpecies?: string }> = () => {
  const [params, setParams] = useState<FisheriesCatchPredictionParams>({
    Fleet: 'EUESP',
    Gear: 'PS',
    Effort: 45.0,
    EffortUnits: 'FHOURS',
    Month: 8,
    Year: 2024,
    Latitude: 2.5,
    Longitude: 55.5,
    SpatialResolution: 1.0,
  });

  const [isSimulating, setIsSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FisheriesCatchPredictionResult | null>(null);

  const handleRun = async () => {
    setIsSimulating(true);
    setError(null);
    try {
      const res = await fisheriesService.predictCatch(params);
      setResult(res);
    } catch (err: any) {
      console.error('Failed to run fisheries catch prediction', err);
      setError(err?.message || 'Catch prediction failed. Please check parameters.');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleReset = () => {
    setParams({
      Fleet: 'EUESP',
      Gear: 'PS',
      Effort: 45.0,
      EffortUnits: 'FHOURS',
      Month: 8,
      Year: 2024,
      Latitude: 2.5,
      Longitude: 55.5,
      SpatialResolution: 1.0,
    });
    setResult(null);
    setError(null);
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
              Fisheries Catch Prediction Simulator (Phase 14.3 V1)
            </h4>
          </div>
          <p className="text-xs text-slate-400">
            Real-time inference using the finalized <strong>XGBoost Regressor</strong> trained on official IOTC surface fisheries data (1970–2022).
          </p>
        </div>

        <Badge variant="cyan" size="sm" className="font-mono self-start sm:self-auto">
          XGBoost V1.0.0 • TotalCatchMT
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-6 space-y-4">
          {/* Fleet & Gear Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Ship className="w-3.5 h-3.5 text-ocean-cyan" />
                Vessel Fleet Flag
              </label>
              <select
                value={params.Fleet}
                onChange={(e) => setParams({ ...params, Fleet: e.target.value })}
                className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan transition-colors font-sans"
              >
                {FLEET_OPTIONS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Anchor className="w-3.5 h-3.5 text-ocean-amber" />
                Fishing Gear
              </label>
              <select
                value={params.Gear}
                onChange={(e) => setParams({ ...params, Gear: e.target.value })}
                className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan transition-colors font-sans"
              >
                {GEAR_OPTIONS.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Effort & Effort Units Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Fishing Effort</span>
                <span className="font-mono text-ocean-cyan font-bold">{params.Effort}</span>
              </div>
              <input
                type="number"
                min={0}
                max={500}
                step={1}
                value={params.Effort}
                onChange={(e) => setParams({ ...params, Effort: Math.max(0, Number(e.target.value)) })}
                className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Effort Units
              </label>
              <select
                value={params.EffortUnits}
                onChange={(e) => setParams({ ...params, EffortUnits: e.target.value })}
                className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan transition-colors font-sans"
              >
                {EFFORT_UNIT_OPTIONS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Month & Year Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-ocean-teal" />
                  Month: <strong>Month {params.Month}</strong>
                </span>
                <span className="font-mono text-slate-400 text-[10px]">
                  {params.Month in [12, 1, 2] ? 'NE Monsoon' : params.Month in [6, 7, 8, 9] ? 'SW Monsoon' : 'Intermonsoon'}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={12}
                step={1}
                value={params.Month}
                onChange={(e) => setParams({ ...params, Month: Number(e.target.value) })}
                className="w-full accent-ocean-teal cursor-pointer h-1.5 bg-marine-900 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Jan (1)</span>
                <span>Jun (6)</span>
                <span>Dec (12)</span>
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Operation Year</span>
                <span className="font-mono text-ocean-cyan font-bold">{params.Year}</span>
              </div>
              <input
                type="number"
                min={1970}
                max={2035}
                value={params.Year}
                onChange={(e) => setParams({ ...params, Year: Number(e.target.value) })}
                className="w-full bg-marine-950/90 border border-marine-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan font-mono"
              />
            </div>
          </div>

          {/* Coordinates Slider Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center gap-1">
                  <Compass className="w-3.5 h-3.5 text-ocean-cyan" />
                  Latitude (°N)
                </span>
                <span className="font-mono text-ocean-cyan font-bold">{params.Latitude.toFixed(1)}°N</span>
              </div>
              <input
                type="range"
                min={-30.0}
                max={25.0}
                step={0.5}
                value={params.Latitude}
                onChange={(e) => setParams({ ...params, Latitude: Number(e.target.value) })}
                className="w-full accent-ocean-cyan cursor-pointer h-1.5 bg-marine-900 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>-30.0°S</span>
                <span>0.0° Equator</span>
                <span>+25.0°N</span>
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center gap-1">
                  <Compass className="w-3.5 h-3.5 text-ocean-teal" />
                  Longitude (°E)
                </span>
                <span className="font-mono text-ocean-teal font-bold">{params.Longitude.toFixed(1)}°E</span>
              </div>
              <input
                type="range"
                min={40.0}
                max={100.0}
                step={0.5}
                value={params.Longitude}
                onChange={(e) => setParams({ ...params, Longitude: Number(e.target.value) })}
                className="w-full accent-ocean-teal cursor-pointer h-1.5 bg-marine-900 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>40.0°E (West)</span>
                <span>70.0°E</span>
                <span>100.0°E (East)</span>
              </div>
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
              <span>{isSimulating ? 'Predicting Catch (XGBoost V1)...' : 'Run V1 Catch Prediction'}</span>
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

          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
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
                  <h5 className="text-sm font-semibold text-white mt-0.5">
                    {result.input_summary.fleet} • {result.input_summary.gear} • {result.input_summary.season}
                  </h5>
                </div>
                <Badge variant="teal" size="sm">
                  {result.model_version ? `Model V${result.model_version}` : 'V1 Production'}
                </Badge>
              </div>

              {/* Primary Output Display */}
              <div className="p-4 rounded-xl bg-marine-900/90 border border-marine-800 space-y-2">
                <span className="text-[10px] font-sans text-slate-400 uppercase tracking-wider block">
                  Predicted Total Catch (XGBoost V1)
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-mono font-black text-ocean-cyan tracking-tight">
                    {result.predicted_catch_mt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="text-sm font-semibold text-slate-300 font-mono">{result.unit}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-400 pt-2 border-t border-marine-800/80">
                  <span>Effort: <strong className="text-slate-200">{result.input_summary.effort} {result.input_summary.effort_units}</strong></span>
                  <span>Log Effort: <strong className="text-ocean-teal">{result.input_summary.log_effort}</strong></span>
                  <span>Coordinates: <strong className="text-slate-200">{result.input_summary.latitude}°N, {result.input_summary.longitude}°E</strong></span>
                  <span>Monsoon: <strong className="text-ocean-amber">{result.input_summary.season}</strong></span>
                </div>
              </div>

              {/* Advisory & Scientific Disclaimer */}
              <div className="p-3 rounded-lg bg-marine-900/50 border border-marine-850 text-xs text-slate-300 space-y-1.5 leading-relaxed">
                <span className="font-semibold text-white block">Scientific Decision Support Notice:</span>
                <p>{result.disclaimer}</p>
              </div>

              <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between pt-1">
                <span>Model: <strong>{result.model}</strong></span>
                <span>Target: <strong>{result.target_variable}</strong></span>
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
                  Adjust operational stratum parameters (Fleet, Gear, Effort, Month, Location) and click <strong>Run V1 Catch Prediction</strong> to generate real XGBoost predictions.
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

