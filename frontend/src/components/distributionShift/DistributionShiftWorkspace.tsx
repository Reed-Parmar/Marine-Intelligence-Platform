import React, { useState, useEffect } from 'react';
import {
  DistributionShiftPredictionRequest,
  DistributionShiftPredictionResponse,
  CANONICAL_ARABIAN_SEA_SECTORS,
  SUPPORTED_PRIORITY_SPECIES,
  MONTH_NAMES,
} from '../../types/distributionShift';
import { distributionShiftService } from '../../services/distributionShift';
import { DistributionShiftMap } from './DistributionShiftMap';
import { EvidenceDrawer } from './EvidenceDrawer';
import { Card, CardHeader } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { useToast } from '../../context/ToastContext';
import {
  Compass,
  Calendar,
  Thermometer,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  ShieldCheck,
  TrendingUp,
  Fish,
} from 'lucide-react';

interface DistributionShiftWorkspaceProps {
  initialSpecies?: string;
  initialSector?: string;
  className?: string;
}

export const DistributionShiftWorkspace: React.FC<DistributionShiftWorkspaceProps> = ({
  initialSpecies = 'Sardinella longiceps',
  initialSector = 'Malabar Upwelling Shelf',
  className = '',
}) => {
  const { addToast } = useToast();

  // Form State initialized with default Arabian Sea demo values
  const [species, setSpecies] = useState<string>(initialSpecies);
  const [currentSector, setCurrentSector] = useState<string>(initialSector);
  const [latitude, setLatitude] = useState<number>(10.5);
  const [longitude, setLongitude] = useState<number>(75.5);
  const [month, setMonth] = useState<number>(4); // April (Pre-Monsoon)
  const [forecastHorizon, setForecastHorizon] = useState<number>(2); // 2 months -> June (SW Monsoon)
  const [depth, setDepth] = useState<number | ''>(35.0);

  // Optional Physicochemical CTD Sensors
  const [showSensors, setShowSensors] = useState<boolean>(false);
  const [sst, setSst] = useState<number | ''>(29.5);
  const [salinity, setSalinity] = useState<number | ''>(35.2);
  const [dissolvedOxygen, setDissolvedOxygen] = useState<number | ''>(4.8);
  const [chlorophyll, setChlorophyll] = useState<number | ''>(1.5);

  // Async & Response States
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [prediction, setPrediction] = useState<DistributionShiftPredictionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState<boolean>(false);

  // Sync sector coordinates when sector dropdown changes
  const handleSectorChange = (sector: string) => {
    setCurrentSector(sector);
    if (CANONICAL_ARABIAN_SEA_SECTORS[sector]) {
      const [lat, lon] = CANONICAL_ARABIAN_SEA_SECTORS[sector];
      setLatitude(lat);
      setLongitude(lon);
    }
  };

  // Execute prediction request against real FastAPI backend
  const handlePredict = async () => {
    setIsLoading(true);
    setErrorMsg(null);

    const payload: DistributionShiftPredictionRequest = {
      species_id: species,
      current_sector: currentSector,
      latitude: Number(latitude),
      longitude: Number(longitude),
      month: Number(month),
      forecast_horizon_months: Number(forecastHorizon),
      mean_depth_meters: depth !== '' ? Number(depth) : null,
      sst_celsius: sst !== '' ? Number(sst) : null,
      salinity_psu: salinity !== '' ? Number(salinity) : null,
      dissolved_oxygen_mgl: dissolvedOxygen !== '' ? Number(dissolvedOxygen) : null,
      chlorophyll_mg_m3: chlorophyll !== '' ? Number(chlorophyll) : null,
    };

    try {
      const res = await distributionShiftService.predictDistributionShift(payload);
      setPrediction(res);
      addToast(
        'success',
        'Seasonal Distribution Shift Forecasted',
        `Predicted primary dispersal to ${res.top_prediction.sector} (${(res.top_prediction.probability * 100).toFixed(1)}% propensity).`
      );
    } catch (err: any) {
      console.error('Failed to forecast distribution shift:', err);
      const msg = err.message || 'An error occurred while executing the distribution shift model.';
      setErrorMsg(msg);
      addToast('error', 'Prediction Failed', msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Run initial prediction on mount for seamless demo load
  useEffect(() => {
    handlePredict();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getConfidenceBadgeVariant = (level: string): 'teal' | 'amber' | 'coral' => {
    switch (level) {
      case 'HIGH':
        return 'teal';
      case 'MODERATE':
        return 'amber';
      case 'LOW':
      default:
        return 'coral';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-ocean-cyan/10 border border-ocean-cyan/30 text-ocean-cyan">
              <Compass className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                Seasonal Species Distribution Shift Studio
                <Badge variant="cyan" size="sm">
                  Full XGBoost • Markov Prior
                </Badge>
              </h3>
              <p className="text-xs text-slate-400">
                Eulerian population movement propensity forecasting across 7 Arabian Sea ecological sectors.
              </p>
            </div>
          </div>
        </div>

        {prediction && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEvidenceOpen(true)}
              leftIcon={<ShieldCheck className="w-4 h-4 text-ocean-cyan" />}
            >
              Inspect Evidence & Model Trace
            </Button>
          </div>
        )}
      </div>

      {/* Control Form & Config Card */}
      <Card className="p-5 border-marine-800 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Species Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Fish className="w-3.5 h-3.5 text-ocean-cyan" />
              Target Marine Species
            </label>
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2.5 text-white focus:outline-none focus:border-ocean-cyan transition-colors"
            >
              {SUPPORTED_PRIORITY_SPECIES.map((sp) => (
                <option key={sp.id} value={sp.id}>
                  {sp.name} ({sp.category})
                </option>
              ))}
            </select>
          </div>

          {/* 2. Source Ecological Sector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-ocean-cyan" />
              Arabian Sea Source Sector
            </label>
            <select
              value={currentSector}
              onChange={(e) => handleSectorChange(e.target.value)}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2.5 text-white focus:outline-none focus:border-ocean-cyan transition-colors"
            >
              {Object.keys(CANONICAL_ARABIAN_SEA_SECTORS).map((sec) => (
                <option key={sec} value={sec}>
                  {sec}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Observation Month */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-ocean-cyan" />
              Source Month (Monsoon Phase)
            </label>
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2.5 text-white focus:outline-none focus:border-ocean-cyan transition-colors"
            >
              {MONTH_NAMES.map((m, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  Month {idx + 1}: {m}
                </option>
              ))}
            </select>
          </div>

          {/* 4. Forecast Horizon */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-ocean-cyan" />
                Forecast Horizon
              </label>
              <span className="text-xs font-mono font-bold text-ocean-cyan">
                +{forecastHorizon} {forecastHorizon === 1 ? 'Month' : 'Months'}
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={6}
              step={1}
              value={forecastHorizon}
              onChange={(e) => setForecastHorizon(Number(e.target.value))}
              className="w-full h-2 bg-marine-950 rounded-lg appearance-none cursor-pointer accent-ocean-cyan"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>+1m</span>
              <span>+2m (Default)</span>
              <span>+3m</span>
              <span>+6m</span>
            </div>
          </div>
        </div>

        {/* Spatial Coordinates & Bathymetry */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-marine-800/80">
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">
              Latitude (°N: 6.0 - 24.0)
            </label>
            <input
              type="number"
              step="0.1"
              min="6.0"
              max="24.0"
              value={latitude}
              onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">
              Longitude (°E: 65.0 - 78.5)
            </label>
            <input
              type="number"
              step="0.1"
              min="65.0"
              max="78.5"
              value={longitude}
              onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">
              Seafloor Depth (m, optional)
            </label>
            <input
              type="number"
              placeholder="e.g. 35.0"
              value={depth}
              onChange={(e) => setDepth(e.target.value === '' ? '' : parseFloat(e.target.value))}
              className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
            />
          </div>
        </div>

        {/* Collapsible Optional In-Situ CTD Sensor Inputs */}
        <div className="pt-2 border-t border-marine-800/60">
          <button
            type="button"
            onClick={() => setShowSensors(!showSensors)}
            className="flex items-center gap-1.5 text-xs text-ocean-cyan hover:text-cyan-300 font-medium transition-colors"
          >
            <Thermometer className="w-3.5 h-3.5" />
            <span>{showSensors ? 'Hide Optional In-Situ CTD Sensors' : 'Add Optional In-Situ CTD Sensors (SST, Salinity, DO, Chlorophyll)'}</span>
            {showSensors ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showSensors && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 animate-fade-in">
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">SST (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="29.5"
                  value={sst}
                  onChange={(e) => setSst(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Salinity (PSU)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="35.2"
                  value={salinity}
                  onChange={(e) => setSalinity(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Dissolved O₂ (mg/L)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="4.8"
                  value={dissolvedOxygen}
                  onChange={(e) => setDissolvedOxygen(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Chlorophyll-a (mg/m³)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="1.5"
                  value={chlorophyll}
                  onChange={(e) => setChlorophyll(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full text-xs rounded-lg bg-marine-950 border border-marine-700 p-2 text-white font-mono"
                />
              </div>
            </div>
          )}
        </div>

        {/* Action Button & Disclaimer Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-marine-800">
          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-ocean-cyan shrink-0" />
            <span>Missing sensors are handled via native NaN tree routing without zero-imputation.</span>
          </div>

          <Button
            variant="glow"
            size="md"
            onClick={handlePredict}
            disabled={isLoading}
            leftIcon={<Sparkles className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
          >
            {isLoading ? 'Analyzing seasonal distribution...' : 'Forecast Distribution Shift'}
          </Button>
        </div>
      </Card>

      {/* Error Message Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-200 flex items-center gap-2.5 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Results & Interactive Map Grid */}
      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Probability Breakdown & Predictions (5 Cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Primary Prediction Card */}
            <Card className="p-5 border-ocean-cyan/40 bg-marine-950/90 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                  Primary Predicted Dispersal
                </span>
                <Badge variant={getConfidenceBadgeVariant(prediction.confidence_level)} size="sm">
                  {prediction.confidence_level} CONFIDENCE
                </Badge>
              </div>

              <div className="flex items-baseline justify-between">
                <h4 className="text-lg font-bold text-white tracking-wide">
                  {prediction.top_prediction.sector}
                </h4>
                <span className="text-2xl font-mono font-black text-ocean-cyan">
                  {(prediction.top_prediction.probability * 100).toFixed(1)}%
                </span>
              </div>

              {/* Temporal Transition Indicator */}
              <div className="p-3 rounded-lg bg-marine-900/80 border border-marine-800 text-xs space-y-1">
                <div className="flex justify-between items-center text-slate-300">
                  <span>Source Regime:</span>
                  <span className="font-semibold text-white">
                    {MONTH_NAMES[prediction.forecast.source_month - 1]} ({prediction.forecast.source_season.season_name.split(' ')[0]})
                  </span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>Forecast Target (+{prediction.forecast_horizon_months}m):</span>
                  <span className="font-semibold text-emerald-400">
                    {MONTH_NAMES[prediction.forecast.target_month - 1]} ({prediction.forecast.target_season.season_name.split(' ')[0]})
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 pt-1">
                {prediction.confidence_tier}
              </p>
            </Card>

            {/* 7-Sector Horizontal Probability Distribution */}
            <Card className="p-5 border-marine-800 space-y-3">
              <CardHeader
                title="7-Sector Movement Propensity"
                subtitle="Full Bayesian posterior probability distribution"
              />

              <div className="space-y-2.5 pt-1">
                {Object.entries(prediction.probability_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .map(([sec, prob], rank) => {
                    const isTop = rank === 0;
                    const percent = (prob * 100).toFixed(1);

                    return (
                      <div key={sec} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-1.5">
                            <span className="w-4 h-4 rounded-full bg-marine-800 text-[10px] font-mono flex items-center justify-center text-slate-400">
                              {rank + 1}
                            </span>
                            <span className={`font-medium ${isTop ? 'text-ocean-cyan font-bold' : 'text-slate-300'}`}>
                              {sec}
                            </span>
                          </div>
                          <span className="font-mono font-bold text-slate-200">
                            {percent}%
                          </span>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full h-2 rounded-full bg-marine-900 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isTop
                                ? 'bg-gradient-to-r from-cyan-500 to-ocean-cyan shadow-[0_0_8px_#00f0ff]'
                                : rank < 3
                                ? 'bg-gradient-to-r from-blue-500 to-cyan-400'
                                : 'bg-slate-700'
                            }`}
                            style={{ width: `${Math.max(2, prob * 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>

              {/* Markov Prior Comparison */}
              <div className="p-3 rounded-lg bg-marine-950 border border-marine-800 text-[11px] text-slate-400 flex items-center justify-between">
                <div>
                  <span className="block text-slate-500">Historical Markov Baseline:</span>
                  <span className="font-semibold text-slate-200">
                    {prediction.markov_baseline_comparison.top_markov_sector} ({(prediction.markov_baseline_comparison.markov_probability * 100).toFixed(1)}%)
                  </span>
                </div>
                <Badge variant="slate" size="sm">
                  {prediction.markov_baseline_comparison.fallback_description.split(':')[0]}
                </Badge>
              </div>
            </Card>
          </div>

          {/* Right Column: Interactive Leaflet Map (7 Cols) */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="p-4 border-marine-800 h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Arabian Sea Spatial Dispersal Vectors
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-ocean-cyan">
                  {prediction.source_coordinates.latitude.toFixed(1)}°N, {prediction.source_coordinates.longitude.toFixed(1)}°E
                </span>
              </div>

              <div className="flex-1 min-h-[480px]">
                <DistributionShiftMap
                  prediction={prediction}
                  onSelectSector={(sec) => {
                    handleSectorChange(sec);
                  }}
                />
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Evidence & Scientific Validation Trace Drawer */}
      <EvidenceDrawer
        isOpen={isEvidenceOpen}
        onClose={() => setIsEvidenceOpen(false)}
        prediction={prediction}
      />
    </div>
  );
};
