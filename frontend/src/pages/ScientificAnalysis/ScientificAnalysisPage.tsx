import React, { useEffect, useState } from 'react';
import { analysisService } from '../../services/analysis';
import { AnalysisResultData, AnalysisParameterConfig } from '../../types/analysis';
import { ParameterForm } from '../../components/analysis/ParameterForm';
import { StatisticalSummary } from '../../components/analysis/StatisticalSummary';
import { ProvenanceTrace } from '../../components/analysis/ProvenanceTrace';
import { CorrelationChart } from '../../components/charts/CorrelationChart';
import { Card, CardHeader } from '../../components/ui/Card';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../context/ToastContext';
import { Microscope, Play, Sparkles, BookOpen, Layers } from 'lucide-react';

export const ScientificAnalysisPage: React.FC = () => {
  const { addToast } = useToast();
  const [analysisResult, setAnalysisResult] = useState<AnalysisResultData | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  const [parameters, setParameters] = useState<AnalysisParameterConfig>({
    analysisType: 'cross_domain_correlation',
    independentVariable: 'sea_surface_temperature',
    dependentVariable: 'species_richness',
    region: 'Arabian Sea',
    depthMin: 0,
    depthMax: 50,
    transformation: 'none'
  });

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const res = await analysisService.getAnalysisById('analysis-sst-richness');
        setAnalysisResult(res);
      } catch (err) {
        console.error('Failed to load initial analysis', err);
      } finally {
        setIsLoadingInitial(false);
      }
    };
    loadInitial();
  }, []);

  const handleRunAnalysis = async () => {
    setIsRunning(true);
    try {
      const res = await analysisService.runCorrelationAnalysis(parameters);
      setAnalysisResult(res);
      addToast('success', 'Analysis Execution Completed', `Computed OLS regression for ${parameters.independentVariable} vs ${parameters.dependentVariable}.`);
    } catch (err: any) {
      addToast('error', 'Execution Failed', err.message);
    } finally {
      setIsRunning(false);
    }
  };

  if (isLoadingInitial || !analysisResult) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Microscope className="w-5 h-5 text-ocean-cyan" />
            Scientific Cross-Domain Analysis Studio
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compute linear and non-linear regressions across physical oceanography, fisheries CPUE, and species richness.
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <ParameterForm
        parameters={parameters}
        onChange={setParameters}
        onRunAnalysis={handleRunAnalysis}
        isRunning={isRunning}
      />

      {/* Main Analysis Result Canvas */}
      <div className="space-y-6 animate-slide-up">
        {/* Regression Scatter Plot & Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Scatter + Trend Line */}
          <Card className="lg:col-span-2 p-5 space-y-4">
            <CardHeader
              title={analysisResult.title}
              subtitle={`Sample Size N = ${analysisResult.statistics.sampleSize} transects • R² = ${(analysisResult.statistics.rSquared * 100).toFixed(1)}%`}
            />
            <CorrelationChart
              scatterPoints={analysisResult.scatterPoints}
              regressionLine={analysisResult.regressionLine}
              xLabel={parameters.independentVariable.replace(/_/g, ' ').toUpperCase()}
              yLabel={parameters.dependentVariable.replace(/_/g, ' ').toUpperCase()}
              height={340}
            />
          </Card>

          {/* Right 1 Col: Ecological Interpretation */}
          <Card className="p-5 flex flex-col justify-between space-y-4 bg-marine-900/70 border-ocean-cyan/30">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-ocean-cyan">
                <BookOpen className="w-4 h-4" />
                <span>Ecological Interpretation</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                {analysisResult.ecologicalInterpretation}
              </p>
              <p className="text-[11px] text-slate-400 leading-relaxed border-t border-marine-800 pt-3">
                {analysisResult.summaryText}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-marine-950/80 border border-marine-800 text-[11px] text-slate-400">
              <span className="font-semibold text-white">Significance: </span>
              Pearson correlation r = {analysisResult.statistics.pearsonR} indicates a robust cross-domain linkage.
            </div>
          </Card>
        </div>

        {/* Statistical Metrics Breakdown */}
        <StatisticalSummary statistics={analysisResult.statistics} />

        {/* Lineage & Provenance Trace */}
        <ProvenanceTrace provenance={analysisResult.provenance} />
      </div>
    </div>
  );
};
